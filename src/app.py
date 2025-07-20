import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models.models import db, StrategyPosition, InternalPasswordManager, User, UserStrategy, init_redis
from config import SQLALCHEMY_DATABASE_URI, API_HOST, API_PORT, CRYPTO_AUTH_CONFIG, REDIS_CONFIG
from auth.simple_crypto_auth import SimpleCryptoAuth, require_auth
import auth.simple_crypto_auth as auth_module
from functools import wraps
from datetime import datetime, timedelta
import secrets

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 设置会话密钥
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    
    db.init_app(app)
    
    # 初始化Flask-Login（如果available）
    try:
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'login'
        login_manager.login_message = '请先登录访问此页面'
        login_manager.login_message_category = 'info'
        
        # 创建简单的用户类
        class FlaskUser(UserMixin):
            def __init__(self, username, is_superuser=False):
                self.id = username
                self.username = username
                self.is_superuser = is_superuser
        
        @login_manager.user_loader
        def load_user(username):
            user_data = User.get_user_by_username(username)
            if user_data:
                return FlaskUser(user_data['username'], user_data['is_superuser'])
            return None
        
        app.flask_user_class = FlaskUser
        app.has_flask_login = True
        print("✓ Flask-Login 认证系统已启用")
        
    except ImportError:
        app.has_flask_login = False
        print("⚠️  Flask-Login 未安装，使用Session认证")
    
    # 初始化Redis
    init_redis(REDIS_CONFIG)
    
    # 初始化认证系统
    init_auth_system()
    
    with app.app_context():
        # 检查并初始化数据库
        init_database_if_needed()
    
    return app

def init_database_if_needed():
    """检查并初始化数据库（如果需要）"""
    try:
        # 尝试创建所有表
        db.create_all()
        print("✓ 数据库表结构检查完成")
        
        # 创建默认超级管理员
        User.create_default_superuser()
        
        # 检查是否需要初始化默认数据
        # 注意：现在使用管理员用户密码作为内部API密码，无需单独的internal_passwords表
        
        # 检查是否有策略数据，如果没有则创建示例策略
        if StrategyPosition.query.count() == 0:
            example_positions = [
                {
                    'code': '000001.SZ',
                    'name': '平安银行',
                    'volume': 1000,
                    'cost': 12.50
                },
                {
                    'code': '600000.SH', 
                    'name': '浦发银行',
                    'volume': 500,
                    'cost': 8.20
                }
            ]
            
            StrategyPosition.update_positions('example_strategy', example_positions)
            print("✓ 已创建示例策略数据: example_strategy")
        
        print("✓ 数据库初始化检查完成")
        
    except Exception as e:
        print(f"⚠️  数据库初始化检查失败: {e}")
        print("请手动运行 python init_database.py 进行数据库初始化")
        print("或执行 database_schema.sql 文件进行数据库创建")

def init_auth_system():
    """初始化认证系统"""
    if CRYPTO_AUTH_CONFIG.get('ENABLED', True):
        # 现在使用基于数据库的加密认证
        print("基于数据库的加密认证系统已启用")
        print("认证时将从数据库的 users 表中读取每个用户的密钥对")
        
        # 保留全局 crypto_auth 实例的初始化以兼容可能的其他用途
        try:
            # 优先使用文件路径配置
            if 'PRIVATE_KEY_FILE' in CRYPTO_AUTH_CONFIG and 'PUBLIC_KEY_FILE' in CRYPTO_AUTH_CONFIG:
                private_key_file = CRYPTO_AUTH_CONFIG['PRIVATE_KEY_FILE']
                public_key_file = CRYPTO_AUTH_CONFIG['PUBLIC_KEY_FILE']
                
                # 设置全局认证实例（从文件读取）- 主要用于兼容性
                auth_module.crypto_auth = SimpleCryptoAuth(
                    private_key_file=private_key_file,
                    public_key_file=public_key_file
                )
                print(f"全局认证实例已初始化（兼容用途，从文件: {private_key_file}, {public_key_file}）")
            
            # 兼容旧的字符串配置方式
            elif 'PRIVATE_KEY' in CRYPTO_AUTH_CONFIG and 'PUBLIC_KEY' in CRYPTO_AUTH_CONFIG:
                private_key = CRYPTO_AUTH_CONFIG['PRIVATE_KEY']
                public_key = CRYPTO_AUTH_CONFIG['PUBLIC_KEY']
                
                # 设置全局认证实例（从字符串读取）- 主要用于兼容性
                auth_module.crypto_auth = SimpleCryptoAuth(private_key, public_key)
                print("全局认证实例已初始化（兼容用途，从配置字符串）")
            
            else:
                print("未找到全局密钥配置，仅使用数据库密钥认证")
                auth_module.crypto_auth = None
                
        except Exception as e:
            print(f"全局认证实例初始化失败: {e}")
            print("将仅使用数据库密钥认证（这是推荐的方式）")
            auth_module.crypto_auth = None
    else:
        # 禁用加密认证，使用简单API密钥
        print("加密认证已禁用，使用简单API密钥认证")
        if not CRYPTO_AUTH_CONFIG.get('SIMPLE_API_KEY'):
            print("警告: 未配置简单API密钥，API将不安全！")

def require_internal_password(f):
    """内部API密码验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取密码
        password = None
        
        # 尝试从请求头获取密码
        if 'X-Internal-Password' in request.headers:
            password = request.headers['X-Internal-Password']
        # 尝试从请求体获取密码
        elif request.is_json and request.get_json():
            data = request.get_json()
            password = data.get('internal_password')
        # 尝试从表单数据获取密码
        elif request.form:
            password = request.form.get('internal_password')
        
        if not password:
            return jsonify({
                'error': '缺少内部密码',
                'message': '请在请求头X-Internal-Password或请求体internal_password字段中提供密码'
            }), 401
        
        # 验证密码
        if not InternalPasswordManager.verify_password(password):
            return jsonify({
                'error': '密码验证失败',
                'message': '内部密码不正确'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def web_login_required(f):
    """Web页面登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            # 使用Flask-Login
            try:
                if not current_user.is_authenticated:
                    return redirect(url_for('login'))
                # 更新用户活跃时间
                User.update_activity_time(current_user.username)
            except:
                # Flask-Login不可用，使用Session
                if 'user_id' not in session:
                    return redirect(url_for('login'))
                User.update_activity_time(session['user_id'])
        else:
            # 使用Session认证
            if 'user_id' not in session:
                return redirect(url_for('login'))
            # 更新用户活跃时间
            User.update_activity_time(session['user_id'])
        
        return f(*args, **kwargs)
    return decorated_function

def superuser_required(f):
    """超级管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            # 使用Flask-Login
            try:
                if not current_user.is_authenticated:
                    return redirect(url_for('login'))
                if not current_user.is_superuser:
                    flash('您没有访问此页面的权限', 'error')
                    return redirect(url_for('index'))
            except:
                # Flask-Login不可用，使用Session
                if 'user_id' not in session:
                    return redirect(url_for('login'))
                user_data = User.get_user_by_username(session['user_id'])
                if not user_data or not user_data.get('is_superuser', False):
                    flash('您没有访问此页面的权限', 'error')
                    return redirect(url_for('index'))
        else:
            # 使用Session认证
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user_data = User.get_user_by_username(session['user_id'])
            if not user_data or not user_data.get('is_superuser', False):
                flash('您没有访问此页面的权限', 'error')
                return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

app = create_app()

@app.route('/api/v1/positions/update', methods=['POST'])
@require_auth  # 使用统一认证装饰器
def update_positions():
    try:
        data = request.get_json()
        if not data or 'strategy_name' not in data or 'positions' not in data:
            return jsonify({'error': '无效的数据格式'}), 400
            
        StrategyPosition.update_positions(data['strategy_name'], data['positions'])
        return jsonify({
            'message': '持仓更新成功',
            'client_id': getattr(request, 'client_id', 'unknown'),
            'auth_type': getattr(request, 'auth_type', 'unknown')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/update/internal', methods=['POST'])
@require_internal_password  # 使用内部密码验证
def update_positions_internal():
    """内部持仓更新接口，使用密码验证而不是RSA验证"""
    try:
        data = request.get_json()
        if not data or 'strategy_name' not in data or 'positions' not in data:
            return jsonify({'error': '无效的数据格式'}), 400
            
        StrategyPosition.update_positions(data['strategy_name'], data['positions'])
        return jsonify({
            'message': '持仓更新成功（内部接口）',
            'strategy_name': data['strategy_name'],
            'positions_count': len(data['positions']),
            'auth_type': 'internal_password'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/auth/info', methods=['GET'])
def get_auth_info():
    """获取认证系统信息"""
    return jsonify({
        'crypto_enabled': CRYPTO_AUTH_CONFIG.get('ENABLED', True),
        'auth_type': 'crypto' if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else 'simple',
        'public_key': CRYPTO_AUTH_CONFIG['PUBLIC_KEY'] if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else None,
        'algorithm': 'RSA-2048' if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else 'API-Key',
        'internal_password_info': InternalPasswordManager.get_current_password_info()
    })

@app.route('/api/v1/internal/password/info', methods=['GET'])
def get_internal_password_info():
    """获取内部密码信息"""
    return jsonify(InternalPasswordManager.get_current_password_info())

@app.route('/api/v1/internal/password/set', methods=['POST'])
def set_internal_password():
    """设置内部密码（修改管理员密码）"""
    try:
        data = request.get_json()
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': '缺少当前密码或新密码'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        if len(new_password) < 6:
            return jsonify({'error': '密码长度至少6位'}), 400
        
        # 使用新的密码管理器设置密码
        InternalPasswordManager.set_password(current_password, new_password)
        return jsonify({
            'message': '密码修改成功',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/user/password/change', methods=['POST'])
@web_login_required
def change_user_password():
    """用户修改自己的密码"""
    try:
        data = request.get_json()
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': '缺少当前密码或新密码'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        if len(new_password) < 6:
            return jsonify({'error': '密码长度至少6位'}), 400
        
        # 获取当前用户名
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            try:
                username = current_user.username
            except:
                username = session.get('user_id')
        else:
            username = session.get('user_id')
        
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        # 验证当前密码
        user = User.authenticate_user(username, current_password)
        if not user:
            return jsonify({'error': '当前密码错误'}), 401
        
        # 修改密码
        user_obj = User.query.filter_by(username=username).first()
        if user_obj:
            user_obj.password_hash = User.hash_password(new_password)
            db.session.commit()
            return jsonify({
                'message': '密码修改成功',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({'error': '用户不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/strategy/<strategy_name>', methods=['GET'])
def get_strategy_positions(strategy_name):
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        if not username or not password:
            return jsonify({'error': '缺少用户名或密码'}), 401

        # 校验用户
        user = User.authenticate_user(username, password)
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401

        # 检查用户是否有权限访问该策略
        if not user.is_superuser:
            if not UserStrategy.check_user_strategy_permission(user.id, strategy_name):
                return jsonify({
                    'error': f'您没有查看策略 "{strategy_name}" 的权限'
                }), 403
            
            # 增加请求计数
            UserStrategy.increment_request_count(user.id, [strategy_name])

        strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
        if strategy:
            return jsonify({
                'positions': [{
                    'code': position['code'],
                    'name': position.get('name', ""),
                    'volume': position['volume'],
                    'cost': position['cost']
                } for position in strategy.positions],
                'update_time': strategy.update_time.strftime('%Y-%m-%d %H:%M:%S') if strategy.update_time else None,
                'user_info': {
                    'username': username,
                    'is_superuser': user.is_superuser,
                    'strategy_name': strategy_name
                }
            })
        else:
            return jsonify({
                'positions': [],
                'update_time': None,
                'user_info': {
                    'username': username,
                    'is_superuser': user.is_superuser,
                    'strategy_name': strategy_name
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/strategy/<strategy_name>/web', methods=['GET'])
@web_login_required
def get_strategy_positions_web(strategy_name):
    """Web页面专用的获取单个策略接口，使用Web会话认证"""
    try:
        # 获取当前登录用户
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            try:
                username = current_user.username
                is_superuser = current_user.is_superuser
            except:
                username = session.get('user_id')
                user_data = User.get_user_by_username(username)
                is_superuser = user_data.get('is_superuser', False) if user_data else False
        else:
            username = session.get('user_id')
            user_data = User.get_user_by_username(username)
            is_superuser = user_data.get('is_superuser', False) if user_data else False

        if not username:
            return jsonify({'error': '用户未登录'}), 401

        user_data = User.get_user_by_username(username)
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404

        # 检查用户是否有权限访问该策略
        if not is_superuser:
            if not UserStrategy.check_user_strategy_permission(user_data['id'], strategy_name):
                return jsonify({
                    'error': f'您没有查看策略 "{strategy_name}" 的权限'
                }), 403
            
            # 增加请求计数
            UserStrategy.increment_request_count(user_data['id'], [strategy_name])

        strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
        if strategy:
            return jsonify({
                'positions': [{
                    'code': position['code'],
                    'name': position.get('name', ""),
                    'volume': position['volume'],
                    'cost': position['cost']
                } for position in strategy.positions],
                'update_time': strategy.update_time.strftime('%Y-%m-%d %H:%M:%S') if strategy.update_time else None,
                'user_info': {
                    'username': username,
                    'is_superuser': is_superuser,
                    'strategy_name': strategy_name
                }
            })
        else:
            return jsonify({
                'positions': [],
                'update_time': None,
                'user_info': {
                    'username': username,
                    'is_superuser': is_superuser,
                    'strategy_name': strategy_name
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/total', methods=['GET'])
def get_total_positions():
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        if not username or not password:
            return jsonify({'error': '缺少用户名或密码'}), 401

        # 校验用户
        user = User.authenticate_user(username, password)
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401

        strategy_names_str = request.args.get('strategies')
        requested_strategies = strategy_names_str.split(',') if strategy_names_str else []

        # 是否包含调整策略，默认包含
        include_adjustments = request.args.get('include_adjustments', 'true').lower() == 'true'

        # 检查用户策略权限
        if requested_strategies:
            # 检查用户是否有权限查看这些策略
            allowed_strategies = []
            for strategy_name in requested_strategies:
                if UserStrategy.check_user_strategy_permission(user.id, strategy_name):
                    allowed_strategies.append(strategy_name)
                else:
                    return jsonify({
                        'error': f'您没有查看策略 "{strategy_name}" 的权限'
                    }), 403
            
            # 增加请求计数
            UserStrategy.increment_request_count(user.id, allowed_strategies)
            
            # 使用允许的策略获取持仓
            result = StrategyPosition.get_total_positions(
                strategy_names=allowed_strategies, 
                include_adjustments=include_adjustments,
                user_id=user.id,
                is_superuser=user.is_superuser
            )
        else:
            # 如果没有指定策略，获取用户所有允许的策略
            user_strategies = UserStrategy.get_user_strategies(user.id)
            if not user_strategies:
                return jsonify({
                    'error': '您没有查看任何策略的权限，请联系管理员'
                }), 403
            
            allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
            
            # 增加请求计数
            UserStrategy.increment_request_count(user.id, allowed_strategy_names)
            
            # 使用用户的所有策略获取持仓
            result = StrategyPosition.get_total_positions(
                strategy_names=allowed_strategy_names, 
                include_adjustments=include_adjustments,
                user_id=user.id,
                is_superuser=user.is_superuser
            )

        return jsonify({
            'positions': result['positions'],
            'update_time': result['update_time'].strftime('%Y-%m-%d %H:%M:%S') if result['update_time'] else None,
            'user_info': {
                'username': username,
                'strategies_accessed': len(requested_strategies) if requested_strategies else len([s['strategy_name'] for s in UserStrategy.get_user_strategies(user.id)])
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/total/web', methods=['GET'])
@web_login_required
def get_total_positions_web():
    """Web页面专用的获取总持仓接口，使用Web会话认证"""
    try:
        # 获取当前登录用户
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            try:
                username = current_user.username
                is_superuser = current_user.is_superuser
            except:
                username = session.get('user_id')
                user_data = User.get_user_by_username(username)
                is_superuser = user_data.get('is_superuser', False) if user_data else False
        else:
            username = session.get('user_id')
            user_data = User.get_user_by_username(username)
            is_superuser = user_data.get('is_superuser', False) if user_data else False

        if not username:
            return jsonify({'error': '用户未登录'}), 401

        user_data = User.get_user_by_username(username)
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404

        # 获取策略参数（虽然Web页面通常不传这个参数）
        strategy_names_str = request.args.get('strategies')
        requested_strategies = strategy_names_str.split(',') if strategy_names_str else []

        # 是否包含调整策略，默认包含
        include_adjustments = request.args.get('include_adjustments', 'true').lower() == 'true'

        # 检查用户策略权限
        if requested_strategies:
            # 检查用户是否有权限查看这些策略
            allowed_strategies = []
            for strategy_name in requested_strategies:
                if UserStrategy.check_user_strategy_permission(user_data['id'], strategy_name):
                    allowed_strategies.append(strategy_name)
                elif not is_superuser:  # 超级用户可以访问任何策略
                    return jsonify({
                        'error': f'您没有查看策略 "{strategy_name}" 的权限'
                    }), 403
            
            # 如果是超级用户且有未授权策略，直接使用请求的策略
            if is_superuser:
                allowed_strategies = requested_strategies
            
            # 增加请求计数（仅对普通用户）
            if not is_superuser:
                UserStrategy.increment_request_count(user_data['id'], allowed_strategies)
            
            # 使用允许的策略获取持仓
            result = StrategyPosition.get_total_positions(
                strategy_names=allowed_strategies, 
                include_adjustments=include_adjustments,
                user_id=user_data['id'],
                is_superuser=is_superuser
            )
        else:
            # 如果没有指定策略，根据用户类型处理
            if is_superuser:
                # 超级用户获取所有策略
                result = StrategyPosition.get_total_positions(
                    strategy_names=None,  # 获取所有策略
                    include_adjustments=include_adjustments,
                    user_id=user_data['id'],
                    is_superuser=is_superuser
                )
            else:
                # 普通用户获取授权的策略
                user_strategies = UserStrategy.get_user_strategies(user_data['id'])
                if not user_strategies:
                    return jsonify({
                        'positions': [],
                        'update_time': None,
                        'user_info': {
                            'username': username,
                            'strategies_accessed': 0,
                            'message': '您没有查看任何策略的权限，请联系管理员'
                        }
                    })
                
                allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
                
                # 增加请求计数
                UserStrategy.increment_request_count(user_data['id'], allowed_strategy_names)
                
                # 使用用户的所有策略获取持仓
                result = StrategyPosition.get_total_positions(
                    strategy_names=allowed_strategy_names,
                    include_adjustments=include_adjustments,
                    user_id=user_data['id'],
                    is_superuser=is_superuser
                )

        return jsonify({
            'positions': result['positions'],
            'update_time': result['update_time'].strftime('%Y-%m-%d %H:%M:%S') if result['update_time'] else None,
            'user_info': {
                'username': username,
                'is_superuser': is_superuser,
                'strategies_accessed': len(requested_strategies) if requested_strategies else (
                    len(StrategyPosition.get_all_strategy_positions(user_id=user_data['id'], is_superuser=is_superuser)) if is_superuser 
                    else len([s['strategy_name'] for s in UserStrategy.get_user_strategies(user_data['id'])])
                )
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/all', methods=['GET'])
def get_all_positions():
    try:
        username = request.args.get('username')
        password = request.args.get('password')
        if not username or not password:
            return jsonify({'error': '缺少用户名或密码'}), 401

        # 校验用户
        user = User.authenticate_user(username, password)
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401

        # 检查是否为超级用户
        if user.is_superuser:
            # 超级用户可以访问所有策略
            positions = StrategyPosition.get_all_strategy_positions(user_id=user.id, is_superuser=True)
            return jsonify({
                'strategies': [{
                    'strategy_name': item['strategy_name'],
                    'positions': [{
                        'code': pos['code'],
                        'name': pos.get('name', ""),
                        'volume': pos['volume'],
                        'cost': pos['cost']
                    } for pos in item['positions']],
                    'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
                } for item in positions],
                'user_info': {
                    'username': username,
                    'is_superuser': True,
                    'total_strategies': len(positions)
                }
            })
        else:
            # 普通用户只能访问授权的策略
            user_strategies = UserStrategy.get_user_strategies(user.id)
            if not user_strategies:
                return jsonify({
                    'error': '您没有查看任何策略的权限，请联系管理员'
                }), 403
            
            allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
            
            # 获取用户可访问的策略持仓（使用权限控制的方法）
            filtered_positions = StrategyPosition.get_all_strategy_positions(user_id=user.id, is_superuser=False)
            
            # 增加请求计数
            UserStrategy.increment_request_count(user.id, allowed_strategy_names)
            
            return jsonify({
                'strategies': [{
                    'strategy_name': item['strategy_name'],
                    'positions': [{
                        'code': pos['code'],
                        'name': pos.get('name', ""),
                        'volume': pos['volume'],
                        'cost': pos['cost']
                    } for pos in item['positions']],
                    'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
                } for item in filtered_positions],
                'user_info': {
                    'username': username,
                    'is_superuser': False,
                    'authorized_strategies': len(allowed_strategy_names),
                    'accessible_strategies': len(filtered_positions)
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/all/web', methods=['GET'])
@web_login_required
def get_all_positions_web():
    """Web页面专用的获取所有策略接口，使用Web会话认证"""
    try:
        # 获取当前登录用户
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            try:
                username = current_user.username
                is_superuser = current_user.is_superuser
            except:
                username = session.get('user_id')
                user_data = User.get_user_by_username(username)
                is_superuser = user_data.get('is_superuser', False) if user_data else False
        else:
            username = session.get('user_id')
            user_data = User.get_user_by_username(username)
            is_superuser = user_data.get('is_superuser', False) if user_data else False

        if not username:
            return jsonify({'error': '用户未登录'}), 401

        user_data = User.get_user_by_username(username)
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404

        # 检查是否为超级用户
        if is_superuser:
            # 超级用户可以访问所有策略
            positions = StrategyPosition.get_all_strategy_positions(user_id=user_data['id'], is_superuser=True)
            return jsonify({
                'strategies': [{
                    'strategy_name': item['strategy_name'],
                    'positions': [{
                        'code': pos['code'],
                        'name': pos.get('name', ""),
                        'volume': pos['volume'],
                        'cost': pos['cost']
                    } for pos in item['positions']],
                    'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
                } for item in positions],
                'user_info': {
                    'username': username,
                    'is_superuser': True,
                    'total_strategies': len(positions)
                }
            })
        else:
            # 普通用户只能访问授权的策略
            user_strategies = UserStrategy.get_user_strategies(user_data['id'])
            if not user_strategies:
                return jsonify({
                    'strategies': [],
                    'user_info': {
                        'username': username,
                        'is_superuser': False,
                        'authorized_strategies': 0,
                        'accessible_strategies': 0,
                        'message': '您没有查看任何策略的权限，请联系管理员'
                    }
                })
            
            allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
            
            # 获取用户可访问的策略持仓（使用权限控制的方法）
            filtered_positions = StrategyPosition.get_all_strategy_positions(user_id=user_data['id'], is_superuser=False)
            
            # 增加请求计数
            UserStrategy.increment_request_count(user_data['id'], allowed_strategy_names)
            
            return jsonify({
                'strategies': [{
                    'strategy_name': item['strategy_name'],
                    'positions': [{
                        'code': pos['code'],
                        'name': pos.get('name', ""),
                        'volume': pos['volume'],
                        'cost': pos['cost']
                    } for pos in item['positions']],
                    'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
                } for item in filtered_positions],
                'user_info': {
                    'username': username,
                    'is_superuser': False,
                    'authorized_strategies': len(allowed_strategy_names),
                    'accessible_strategies': len(filtered_positions)
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == '1'
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        
        user = User.authenticate_user(username, password)
        if user:
            if hasattr(app, 'has_flask_login') and app.has_flask_login:
                # 使用Flask-Login
                try:
                    flask_user = app.flask_user_class(user.username, user.is_superuser)
                    login_user(flask_user, remember=remember, duration=timedelta(days=7 if remember else 1))
                except:
                    # 回退到Session
                    session['user_id'] = user.username
                    session['is_superuser'] = user.is_superuser
                    if remember:
                        session.permanent = True
            else:
                # 使用Session认证
                session['user_id'] = user.username
                session['is_superuser'] = user.is_superuser
                if remember:
                    session.permanent = True
                    
            flash(f'欢迎回来，{user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        strategies_text = request.form.get('strategies', '').strip()
        
        if not username or not password or not confirm_password:
            flash('请填写所有必填字段', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('register.html')
        
        try:
            # 创建普通用户（非管理员）
            user = User.create_user(username, password, is_superuser=False)
            
            # 处理策略权限
            if strategies_text:
                strategy_names = [name.strip() for name in strategies_text.split('\n') if name.strip()]
                for strategy_name in strategy_names:
                    try:
                        UserStrategy.add_user_strategy(user.id, strategy_name)
                    except ValueError as e:
                        # 忽略重复策略的错误
                        pass
                
                if strategy_names:
                    flash(f'用户 {username} 注册成功，已分配 {len(strategy_names)} 个策略权限，请登录', 'success')
                else:
                    flash(f'用户 {username} 注册成功，但未分配任何策略权限，请登录', 'info')
            else:
                flash(f'用户 {username} 注册成功，未分配任何策略权限，请登录', 'info')
                
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('register.html')
        except Exception as e:
            flash(f'注册失败: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if hasattr(app, 'has_flask_login') and app.has_flask_login:
        try:
            logout_user()
        except:
            pass
    
    session.clear()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/')
@web_login_required
def index():
    return render_template('index.html')

@app.route('/adjustment')
@superuser_required
def adjustment():
    return render_template('adjustment.html')

@app.route('/password')
@web_login_required
def password_management():
    return render_template('password.html')

@app.route('/users')
@superuser_required
def user_management():
    users = User.get_active_users_for_superuser()
    
    # 计算统计数据
    stats = {
        'total_users': len(users),
        'active_users': len([u for u in users if u['last_activity_time'] != '无活跃记录']),
        'superusers': len([u for u in users if u['is_superuser']]),
        'users_with_keys': len([u for u in users if u['has_private_key'] and u['has_public_key']])
    }
    
    return render_template('user_management.html', users=users, stats=stats)

@app.route('/users/create', methods=['POST'])
@superuser_required
def create_user():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        is_superuser = request.form.get('is_superuser') == '1'
        
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return redirect(url_for('user_management'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('user_management'))
        
        User.create_user(username, password, is_superuser=is_superuser)
        flash(f'用户 {username} 创建成功', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'创建用户失败: {str(e)}', 'error')
    
    return redirect(url_for('user_management'))

@app.route('/users/delete', methods=['POST'])
@superuser_required
def delete_user():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400
        
        # 不允许删除超级管理员
        user_data = User.get_user_by_username(username)
        if user_data and user_data.get('is_superuser'):
            return jsonify({'error': '不能删除超级管理员账户'}), 403
        
        # 删除用户（实际上是设置为非活跃状态）
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_active = False
            db.session.commit()
            return jsonify({'message': f'用户 {username} 已删除'})
        else:
            return jsonify({'error': '用户不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/user/strategies', methods=['GET'])
@web_login_required
def get_user_strategies():
    """获取当前用户的策略权限和统计信息"""
    try:
        # 获取当前用户名
        if hasattr(app, 'has_flask_login') and app.has_flask_login:
            try:
                username = current_user.username
            except:
                username = session.get('user_id')
        else:
            username = session.get('user_id')
        
        if not username:
            return jsonify({'error': '用户未登录'}), 401
        
        user_data = User.get_user_by_username(username)
        if not user_data:
            return jsonify({'error': '用户不存在'}), 404
        
        # 获取用户策略统计信息
        stats = UserStrategy.get_user_strategy_stats(user_data['id'])
        
        return jsonify({
            'user': {
                'username': username,
                'id': user_data['id']
            },
            'strategies': stats['strategies'],
            'statistics': {
                'total_strategies': stats['total_strategies'],
                'today_requests': stats['today_requests']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/admin/user/<int:user_id>/strategies', methods=['GET', 'POST', 'DELETE'])
@superuser_required
def manage_user_strategies(user_id):
    """管理员管理用户策略权限"""
    try:
        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if request.method == 'GET':
            # 获取用户策略
            stats = UserStrategy.get_user_strategy_stats(user_id)
            return jsonify({
                'user': {
                    'id': user.id,
                    'username': user.username
                },
                'strategies': stats['strategies'],
                'statistics': {
                    'total_strategies': stats['total_strategies'],
                    'today_requests': stats['today_requests']
                }
            })
        
        elif request.method == 'POST':
            # 添加策略权限
            data = request.get_json()
            strategy_name = data.get('strategy_name')
            
            if not strategy_name:
                return jsonify({'error': '策略名称不能为空'}), 400
            
            try:
                UserStrategy.add_user_strategy(user_id, strategy_name)
                return jsonify({
                    'message': f'已为用户 {user.username} 添加策略 {strategy_name} 权限'
                })
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        elif request.method == 'DELETE':
            # 移除策略权限
            data = request.get_json()
            strategy_name = data.get('strategy_name')
            
            if not strategy_name:
                return jsonify({'error': '策略名称不能为空'}), 400
            
            try:
                UserStrategy.remove_user_strategy(user_id, strategy_name)
                return jsonify({
                    'message': f'已移除用户 {user.username} 的策略 {strategy_name} 权限'
                })
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=True
    )