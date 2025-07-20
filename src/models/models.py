from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import hashlib
import redis
import logging
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

db = SQLAlchemy()

# Redis 连接实例
redis_client: Optional[redis.Redis] = None

def init_redis(config):
    """初始化Redis连接"""
    global redis_client
    
    if not config.get('ENABLED', False):
        logger.info("Redis缓存未启用")
        return
    
    try:
        redis_client = redis.Redis(
            host=config.get('HOST', 'localhost'),
            port=config.get('PORT', 6379),
            db=config.get('DB', 0),
            password=config.get('PASSWORD', None),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        # 测试连接
        redis_client.ping()
        logger.info(f"Redis连接成功: {config.get('HOST')}:{config.get('PORT')}")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        redis_client = None

def get_redis_key(prefix, key):
    """生成Redis键名"""
    try:
        from config import REDIS_CONFIG
    except ImportError:
        # 如果相对导入失败，尝试绝对导入
        try:
            from src.config import REDIS_CONFIG
        except ImportError:
            # 如果都失败，使用默认前缀
            REDIS_CONFIG = {'CACHE_PREFIX': 'jq_qmt:'}
    
    cache_prefix = REDIS_CONFIG.get('CACHE_PREFIX', 'jq_qmt:')
    return f"{cache_prefix}{prefix}:{key}"

def set_redis_cache(prefix, key, value, timeout=None):
    """设置Redis缓存"""
    if not redis_client:
        return False
    
    try:
        try:
            from config import REDIS_CONFIG
        except ImportError:
            try:
                from src.config import REDIS_CONFIG
            except ImportError:
                REDIS_CONFIG = {'DEFAULT_TIMEOUT': 86400}
                
        redis_key = get_redis_key(prefix, key)
        if timeout is None:
            timeout = REDIS_CONFIG.get('DEFAULT_TIMEOUT', 86400)
        
        redis_client.setex(redis_key, timeout, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.error(f"设置Redis缓存失败: {e}")
        return False

def get_redis_cache(prefix, key):
    """获取Redis缓存"""
    if not redis_client:
        return None
    
    try:
        redis_key = get_redis_key(prefix, key)
        cached_data = redis_client.get(redis_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"获取Redis缓存失败: {e}")
        return None

def delete_redis_cache(prefix, key):
    """删除Redis缓存"""
    if not redis_client:
        return False
    
    try:
        redis_key = get_redis_key(prefix, key)
        redis_client.delete(redis_key)
        return True
    except Exception as e:
        logger.error(f"删除Redis缓存失败: {e}")
        return False

def publish_redis_message(channel, message):
    """发布Redis消息"""
    if not redis_client:
        return False
    
    try:
        try:
            from config import REDIS_CONFIG
        except ImportError:
            try:
                from src.config import REDIS_CONFIG
            except ImportError:
                REDIS_CONFIG = {'CACHE_PREFIX': 'jq_qmt:'}
                
        cache_prefix = REDIS_CONFIG.get('CACHE_PREFIX', 'jq_qmt:')
        full_channel = f"{cache_prefix}{channel}"
        
        # 确保消息是JSON格式
        if isinstance(message, dict):
            message_str = json.dumps(message, default=str)
        else:
            message_str = str(message)
            
        redis_client.publish(full_channel, message_str)
        logger.debug(f"发布Redis消息到频道 {full_channel}: {message_str[:100]}...")
        return True
    except Exception as e:
        logger.error(f"发布Redis消息失败: {e}")
        return False

def publish_position_update_message(strategy_name, positions):
    """发布持仓更新消息"""
    try:
        message = {
            'action': 'position_update',
            'strategy_name': strategy_name,
            'strategy_names': [strategy_name],  # 兼容QMT端的处理逻辑
            'positions_count': len(positions),
            'positions': positions,  # 包含完整的持仓数据
            'update_time': datetime.now().isoformat(),
            'timestamp': datetime.now().timestamp()
        }
        
        # 发布到持仓更新频道
        publish_redis_message('position_update', message)
        
        # 同时发布到策略更新频道
        strategy_message = {
            'action': 'update',
            'strategy_name': strategy_name,
            'positions': positions,  # 策略更新消息也包含持仓数据
            'positions_count': len(positions),
            'update_time': datetime.now().isoformat(),
            'timestamp': datetime.now().timestamp()
        }
        publish_redis_message('strategy_update', strategy_message)
        
        logger.info(f"已发布策略 {strategy_name} 的更新通知（包含 {len(positions)} 个持仓）")
        
    except Exception as e:
        logger.error(f"发布持仓更新消息失败: {e}")

def publish_strategy_delete_message(strategy_name):
    """发布策略删除消息"""
    try:
        message = {
            'action': 'delete',
            'strategy_name': strategy_name,
            'update_time': datetime.now().isoformat(),
            'timestamp': datetime.now().timestamp()
        }
        
        publish_redis_message('strategy_update', message)
        logger.info(f"已发布策略 {strategy_name} 的删除通知")
        
    except Exception as e:
        logger.error(f"发布策略删除消息失败: {e}")

def publish_total_positions_update(strategy_names=None, include_adjustments=True):
    """发布总持仓数据更新消息"""
    try:
        # 获取最新的总持仓数据
        total_data = StrategyPosition.get_total_positions(strategy_names, include_adjustments)
        
        message = {
            'action': 'total_positions_update',
            'strategy_names': strategy_names if strategy_names else [],
            'include_adjustments': include_adjustments,
            'positions': total_data['positions'],  # 包含完整的总持仓数据
            'positions_count': len(total_data['positions']),
            'update_time': total_data['update_time'].isoformat() if total_data['update_time'] else None,
            'timestamp': datetime.now().timestamp()
        }
        
        # 发布到总持仓更新频道
        publish_redis_message('total_positions_update', message)
        
        logger.info(f"已发布总持仓更新通知（包含 {len(total_data['positions'])} 个持仓）")
        
    except Exception as e:
        logger.error(f"发布总持仓更新消息失败: {e}")

class StrategyPosition(db.Model):
    __tablename__ = 'strategy_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    strategy_name = db.Column(db.String(100), index=True, nullable=False, unique=True)
    positions = db.Column(db.JSON, nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @staticmethod
    def update_positions(strategy_name, positions):
        # 校验策略名称
        if not strategy_name or not isinstance(strategy_name, str):
            raise ValueError("策略名称不能为空且必须为字符串类型")

        # 校验持仓数据
        if not isinstance(positions, list):
            raise ValueError("持仓数据必须为列表类型")

        for pos in positions:
            if not isinstance(pos, dict):
                raise ValueError("持仓数据的每个元素必须为字典类型")
            
            # 检查必需字段
            required_fields = {'code', 'volume', 'cost'}
            if not all(field in pos for field in required_fields):
                raise ValueError(f"持仓数据缺少必需字段: {required_fields}")
            
            # 校验字段类型和值
            if not isinstance(pos['code'], str) or not pos['code']:
                raise ValueError("股票代码必须为非空字符串")
            
            # 对于调整策略，允许负数持仓
            if strategy_name.startswith('ADJUSTMENT_'):
                if not isinstance(pos['volume'], (int, float)):
                    raise ValueError("持仓数量必须为数字")
                # 调整策略允许负数持仓和负成本
                if not isinstance(pos['cost'], (int, float)):
                    raise ValueError("成本价必须为数字")
            else:
                if not isinstance(pos['volume'], (int, float)) or pos['volume'] < 0:
                    raise ValueError("持仓数量必须为非负数")
                
                if not isinstance(pos['cost'], (int, float)) or pos['cost'] <= 0:
                    raise ValueError("成本价必须为正数")
            
            # 校验股票名称字段（可选）
            if 'name' in pos and not isinstance(pos['name'], str):
                raise ValueError("股票名称必须为字符串类型")

        # 执行更新
        strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
        
        if strategy:
            strategy.positions = positions
        else:
            strategy = StrategyPosition(
                strategy_name=strategy_name,
                positions=positions
            )
            db.session.add(strategy)
        
        db.session.commit()
        
        # 更新Redis缓存
        try:
            # 删除相关缓存
            delete_redis_cache('strategy', strategy_name)
            delete_redis_cache('strategy', 'all_strategies')
            delete_redis_cache('strategy', 'total_positions')
            delete_redis_cache('strategy', 'total_positions_no_adj')
            
            # 设置新的缓存
            strategy_data = {
                'strategy_name': strategy_name,
                'positions': positions,
                'update_time': datetime.now().isoformat()
            }
            set_redis_cache('strategy', strategy_name, strategy_data)
            
            # 发布Redis消息通知订阅者
            publish_position_update_message(strategy_name, positions)
            
            # 发布总持仓更新消息（包含和不包含调整策略两种）
            publish_total_positions_update(None, True)   # 包含调整策略
            publish_total_positions_update(None, False)  # 不包含调整策略
            
            logger.info(f"策略 {strategy_name} 的Redis缓存已更新")
        except Exception as e:
            logger.error(f"更新Redis缓存失败: {e}")

    @staticmethod
    def get_strategy_positions(strategy_name):
        # 先尝试从Redis获取
        cached_data = get_redis_cache('strategy', strategy_name)
        if cached_data:
            logger.debug(f"从Redis缓存获取策略 {strategy_name} 的持仓数据")
            return cached_data.get('positions', [])
        
        # Redis中没有，从数据库获取
        strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
        positions = strategy.positions if strategy else []
        
        # 如果找到数据，存入Redis缓存
        if strategy:
            try:
                strategy_data = {
                    'strategy_name': strategy_name,
                    'positions': positions,
                    'update_time': strategy.update_time.isoformat()
                }
                set_redis_cache('strategy', strategy_name, strategy_data)
                logger.debug(f"策略 {strategy_name} 的持仓数据已缓存到Redis")
            except Exception as e:
                logger.error(f"缓存策略数据到Redis失败: {e}")
        
        return positions

    @staticmethod
    def get_all_strategy_positions(user_id=None, is_superuser=False):
        """
        获取所有策略持仓，基于用户权限过滤
        user_id: 用户ID，用于权限控制
        is_superuser: 是否为超级用户
        """
        
        # 1. 先查询MySQL获取用户可访问的策略列表
        if is_superuser:
            # 超级用户可以访问所有策略
            all_strategies = StrategyPosition.query.all()
            allowed_strategy_names = [s.strategy_name for s in all_strategies]
        elif user_id:
            # 普通用户只能访问授权的策略
            user_strategies = UserStrategy.get_user_strategies(user_id)
            if not user_strategies:
                return []
            allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
        else:
            # 没有用户信息，返回空
            return []
        
        # 2. 根据策略名称查询对应的Redis缓存
        result = []
        
        for strategy_name in allowed_strategy_names:
            # 先尝试从Redis获取单个策略数据
            cached_data = get_redis_cache('strategy', strategy_name)
            if cached_data:
                logger.debug(f"从Redis缓存获取策略 {strategy_name} 的持仓数据")
                # Redis中的数据格式需要转换
                try:
                    update_time = datetime.fromisoformat(cached_data['update_time']) if isinstance(cached_data.get('update_time'), str) else cached_data.get('update_time')
                except:
                    update_time = datetime.now()
                
                result.append({
                    'strategy_name': strategy_name,
                    'positions': cached_data.get('positions', []),
                    'update_time': update_time
                })
            else:
                # Redis中没有，从数据库获取并缓存
                strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
                if strategy:
                    result.append({
                        'strategy_name': strategy.strategy_name,
                        'positions': strategy.positions,
                        'update_time': strategy.update_time
                    })
                    
                    # 存入Redis缓存
                    try:
                        strategy_data = {
                            'strategy_name': strategy.strategy_name,
                            'positions': strategy.positions,
                            'update_time': strategy.update_time.isoformat()
                        }
                        set_redis_cache('strategy', strategy_name, strategy_data, timeout=300)  # 5分钟缓存
                        logger.debug(f"策略 {strategy_name} 的持仓数据已缓存到Redis")
                    except Exception as e:
                        logger.error(f"缓存策略数据到Redis失败: {e}")
        
        return result

    @staticmethod
    def get_total_positions(strategy_names=None, include_adjustments=True, user_id=None, is_superuser=False):
        """
        获取总持仓（合并多个策略），基于用户权限过滤
        strategy_names: 指定的策略名称列表
        include_adjustments: 是否包含调整策略
        user_id: 用户ID，用于权限控制
        is_superuser: 是否为超级用户
        """
        
        # 1. 确定要查询的策略列表
        if strategy_names:
            # 如果指定了策略，需要验证权限
            if is_superuser:
                # 超级用户可以访问任何策略
                target_strategies = strategy_names
            elif user_id:
                # 普通用户需要验证权限
                user_strategies = UserStrategy.get_user_strategies(user_id)
                allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
                # 过滤出用户有权限的策略
                target_strategies = [name for name in strategy_names if name in allowed_strategy_names]
            else:
                # 没有用户信息，返回空
                target_strategies = []
        else:
            # 如果没有指定策略，根据用户权限获取所有可访问的策略
            if is_superuser:
                # 超级用户获取所有策略
                all_strategies = StrategyPosition.query.all()
                target_strategies = [s.strategy_name for s in all_strategies]
            elif user_id:
                # 普通用户获取授权的策略
                user_strategies = UserStrategy.get_user_strategies(user_id)
                target_strategies = [s['strategy_name'] for s in user_strategies] if user_strategies else []
            else:
                # 没有用户信息，返回空
                target_strategies = []
        
        # 2. 根据 include_adjustments 参数过滤调整策略
        if not include_adjustments:
            target_strategies = [name for name in target_strategies if not name.startswith('ADJUSTMENT_')]
        
        # 3. 通过策略名称查询对应的Redis缓存或数据库
        all_strategy_data = []
        for strategy_name in target_strategies:
            # 先尝试从Redis获取
            cached_data = get_redis_cache('strategy', strategy_name)
            if cached_data:
                logger.debug(f"从Redis缓存获取策略 {strategy_name} 的持仓数据")
                try:
                    update_time = datetime.fromisoformat(cached_data['update_time']) if isinstance(cached_data.get('update_time'), str) else cached_data.get('update_time')
                except:
                    update_time = datetime.now()
                
                all_strategy_data.append({
                    'strategy_name': strategy_name,
                    'positions': cached_data.get('positions', []),
                    'update_time': update_time
                })
            else:
                # Redis中没有，从数据库获取
                strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
                if strategy:
                    all_strategy_data.append({
                        'strategy_name': strategy.strategy_name,
                        'positions': strategy.positions,
                        'update_time': strategy.update_time
                    })
                    
                    # 存入Redis缓存
                    try:
                        strategy_data = {
                            'strategy_name': strategy.strategy_name,
                            'positions': strategy.positions,
                            'update_time': strategy.update_time.isoformat()
                        }
                        set_redis_cache('strategy', strategy_name, strategy_data, timeout=300)  # 5分钟缓存
                        logger.debug(f"策略 {strategy_name} 的持仓数据已缓存到Redis")
                    except Exception as e:
                        logger.error(f"缓存策略数据到Redis失败: {e}")
        
        # 4. 合并计算总持仓
        total_positions = {}
        latest_update_time = datetime(1970, 1, 1)
        
        for strategy_data in all_strategy_data:
            # 更新最新时间
            if strategy_data['update_time'] and strategy_data['update_time'] > latest_update_time:
                latest_update_time = strategy_data['update_time']
                
            for pos in strategy_data['positions']:
                code = pos['code']
                if code not in total_positions:
                    total_positions[code] = {
                        'code': code,
                        'name': pos.get('name', code),
                        'total_volume': 0,
                        'total_cost': 0
                    }
                
                # 对于调整策略，直接加减持仓数量和成本
                if strategy_data['strategy_name'].startswith('ADJUSTMENT_'):
                    total_positions[code]['total_volume'] += pos['volume']
                    total_positions[code]['total_cost'] += pos['volume'] * pos['cost']
                else:
                    total_positions[code]['total_volume'] += pos['volume']
                    total_positions[code]['total_cost'] += pos['volume'] * pos['cost']
        
        # 5. 计算平均成本并过滤掉持仓为0的股票
        filtered_positions = {}
        for code in total_positions:
            if total_positions[code]['total_volume'] != 0:
                if total_positions[code]['total_volume'] > 0:
                    total_positions[code]['avg_cost'] = (
                        total_positions[code]['total_cost'] / 
                        total_positions[code]['total_volume']
                    )
                else:
                    # 负持仓的情况，显示平均成本
                    total_positions[code]['avg_cost'] = (
                        total_positions[code]['total_cost'] / 
                        total_positions[code]['total_volume']
                    )
                del total_positions[code]['total_cost']
                filtered_positions[code] = total_positions[code]
        
        return {
            'positions': list(filtered_positions.values()),
            'update_time': latest_update_time
        }


class UserStrategy(db.Model):
    """用户-策略关联表，记录用户可查看的策略和当日请求次数"""
    __tablename__ = 'user_strategies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    strategy_name = db.Column(db.String(100), nullable=False, index=True)
    daily_request_count = db.Column(db.Integer, default=0, nullable=False)  # 当日请求次数
    last_request_date = db.Column(db.Date, nullable=True)  # 最后请求日期
    created_time = db.Column(db.DateTime, default=datetime.now)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否激活
    
    # 唯一约束：一个用户对应一个策略只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('user_id', 'strategy_name', name='unique_user_strategy'),
    )
    
    @staticmethod
    def get_user_strategies(user_id):
        """获取用户可查看的策略列表"""
        strategies = UserStrategy.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).all()
        
        return [{
            'strategy_name': s.strategy_name,
            'daily_request_count': s.daily_request_count,
            'last_request_date': s.last_request_date.strftime('%Y-%m-%d') if s.last_request_date else None,
            'created_time': s.created_time.strftime('%Y-%m-%d %H:%M:%S')
        } for s in strategies]
    
    @staticmethod
    def add_user_strategy(user_id, strategy_name):
        """为用户添加策略权限"""
        # 检查是否已存在
        existing = UserStrategy.query.filter_by(
            user_id=user_id, 
            strategy_name=strategy_name
        ).first()
        
        if existing:
            if not existing.is_active:
                # 重新激活已删除的策略
                existing.is_active = True
                existing.updated_time = datetime.now()
                db.session.commit()
                return existing
            else:
                raise ValueError(f"用户已有策略 {strategy_name} 的权限")
        
        # 创建新的策略权限
        user_strategy = UserStrategy(
            user_id=user_id,
            strategy_name=strategy_name
        )
        db.session.add(user_strategy)
        db.session.commit()
        
        # 清除相关缓存
        try:
            delete_redis_cache('user_strategy', f'user_{user_id}')
            logger.info(f"为用户 {user_id} 添加策略 {strategy_name} 权限成功")
        except Exception as e:
            logger.error(f"清除用户策略Redis缓存失败: {e}")
        
        return user_strategy
    
    @staticmethod
    def remove_user_strategy(user_id, strategy_name):
        """移除用户的策略权限"""
        user_strategy = UserStrategy.query.filter_by(
            user_id=user_id, 
            strategy_name=strategy_name,
            is_active=True
        ).first()
        
        if not user_strategy:
            raise ValueError(f"用户没有策略 {strategy_name} 的权限")
        
        user_strategy.is_active = False
        user_strategy.updated_time = datetime.now()
        db.session.commit()
        
        # 清除相关缓存
        try:
            delete_redis_cache('user_strategy', f'user_{user_id}')
            logger.info(f"移除用户 {user_id} 的策略 {strategy_name} 权限成功")
        except Exception as e:
            logger.error(f"清除用户策略Redis缓存失败: {e}")
    
    @staticmethod
    def check_user_strategy_permission(user_id, strategy_name):
        """检查用户是否有某策略的查看权限"""
        user_strategy = UserStrategy.query.filter_by(
            user_id=user_id,
            strategy_name=strategy_name,
            is_active=True
        ).first()
        
        return user_strategy is not None
    
    @staticmethod
    def increment_request_count(user_id, strategy_names):
        """增加用户对策略的请求次数"""
        today = datetime.now().date()
        
        for strategy_name in strategy_names:
            user_strategy = UserStrategy.query.filter_by(
                user_id=user_id,
                strategy_name=strategy_name,
                is_active=True
            ).first()
            
            if user_strategy:
                # 检查是否是新的一天
                if user_strategy.last_request_date != today:
                    # 新的一天，重置计数
                    user_strategy.daily_request_count = 1
                    user_strategy.last_request_date = today
                else:
                    # 同一天，计数+1
                    user_strategy.daily_request_count += 1
                
                user_strategy.updated_time = datetime.now()
        
        db.session.commit()
        
        # 清除相关缓存
        try:
            delete_redis_cache('user_strategy', f'user_{user_id}')
        except Exception as e:
            logger.error(f"清除用户策略Redis缓存失败: {e}")
    
    @staticmethod
    def get_user_strategy_stats(user_id):
        """获取用户策略统计信息"""
        today = datetime.now().date()
        
        strategies = UserStrategy.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        total_strategies = len(strategies)
        today_requests = sum(
            s.daily_request_count for s in strategies 
            if s.last_request_date == today
        )
        
        return {
            'total_strategies': total_strategies,
            'today_requests': today_requests,
            'strategies': [{
                'strategy_name': s.strategy_name,
                'daily_request_count': s.daily_request_count if s.last_request_date == today else 0,
                'last_request_date': s.last_request_date.strftime('%Y-%m-%d') if s.last_request_date else None
            } for s in strategies]
        }


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(64), nullable=False)
    private_key = db.Column(db.Text, nullable=True)  # 存储用户的私钥
    public_key = db.Column(db.Text, nullable=True)   # 存储用户的公钥
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)  # 是否为超级管理员
    is_active = db.Column(db.Boolean, default=True, nullable=False)      # 账户是否激活
    created_time = db.Column(db.DateTime, default=datetime.now)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login_time = db.Column(db.DateTime, nullable=True)              # 最后登录时间
    last_activity_time = db.Column(db.DateTime, nullable=True)           # 最后活跃时间
    login_count = db.Column(db.Integer, default=0)                       # 登录次数
    
    @staticmethod
    def hash_password(password):
        """对密码进行SHA256哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    @staticmethod
    def create_user(username, password, private_key=None, public_key=None, is_superuser=False):
        """创建新用户"""
        if not username or not isinstance(username, str):
            raise ValueError("用户名不能为空且必须为字符串类型")
        
        if not password or not isinstance(password, str):
            raise ValueError("密码不能为空且必须为字符串类型")
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            raise ValueError(f"用户名 {username} 已存在")
        
        password_hash = User.hash_password(password)
        
        user = User(
            username=username,
            password_hash=password_hash,
            private_key=private_key,
            public_key=public_key,
            is_superuser=is_superuser
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 清除相关Redis缓存
        try:
            delete_redis_cache('user', 'all_users')
            delete_redis_cache('user', f'user_{username}')
            logger.info(f"用户 {username} 创建成功")
        except Exception as e:
            logger.error(f"清除用户Redis缓存失败: {e}")
        
        return user
    
    @staticmethod
    def authenticate_user(username, password):
        """验证用户登录"""
        if not username or not password:
            return None
            
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if not user:
            return None
            
        password_hash = User.hash_password(password)
        if user.password_hash != password_hash:
            return None
        
        # 更新登录信息
        user.last_login_time = datetime.now()
        user.last_activity_time = datetime.now()
        user.login_count += 1
        db.session.commit()
        
        # 更新Redis缓存
        try:
            delete_redis_cache('user', f'user_{username}')
            user_data = {
                'id': user.id,
                'username': user.username,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'last_login_time': user.last_login_time.isoformat() if user.last_login_time else None,
                'last_activity_time': user.last_activity_time.isoformat() if user.last_activity_time else None,
                'login_count': user.login_count
            }
            set_redis_cache('user', f'user_{username}', user_data)
        except Exception as e:
            logger.error(f"更新用户Redis缓存失败: {e}")
        
        return user
    
    @staticmethod
    def update_activity_time(username):
        """更新用户活跃时间"""
        user = User.query.filter_by(username=username, is_active=True).first()
        if user:
            user.last_activity_time = datetime.now()
            db.session.commit()
            
            # 更新Redis缓存
            try:
                delete_redis_cache('user', f'user_{username}')
            except Exception as e:
                logger.error(f"清除用户Redis缓存失败: {e}")
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户信息"""
        # 先尝试从Redis获取
        cached_data = get_redis_cache('user', f'user_{username}')
        if cached_data:
            logger.debug(f"从Redis缓存获取用户 {username} 的信息")
            return cached_data
        
        # Redis中没有，从数据库获取
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return None
            
        user_data = {
            'id': user.id,
            'username': user.username,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'created_time': user.created_time.isoformat(),
            'last_login_time': user.last_login_time.isoformat() if user.last_login_time else None,
            'last_activity_time': user.last_activity_time.isoformat() if user.last_activity_time else None,
            'login_count': user.login_count,
            'has_private_key': bool(user.private_key),
            'has_public_key': bool(user.public_key)
        }
        
        # 存入Redis缓存
        try:
            set_redis_cache('user', f'user_{username}', user_data)
            logger.debug(f"用户 {username} 的信息已缓存到Redis")
        except Exception as e:
            logger.error(f"缓存用户信息到Redis失败: {e}")
        
        return user_data
    
    @staticmethod
    def get_user_keys(username):
        """获取用户的密钥对"""
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            return None, None
        return user.private_key, user.public_key
    
    @staticmethod
    def update_user_keys(username, private_key, public_key):
        """更新用户的密钥对"""
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            raise ValueError(f"用户 {username} 不存在")
        
        user.private_key = private_key
        user.public_key = public_key
        user.updated_time = datetime.now()
        db.session.commit()
        
        # 清除Redis缓存
        try:
            delete_redis_cache('user', f'user_{username}')
            logger.info(f"用户 {username} 的密钥已更新")
        except Exception as e:
            logger.error(f"清除用户Redis缓存失败: {e}")
    
    @staticmethod
    def update_user_status(username, is_active):
        """更新用户状态（激活/禁用）"""
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 不允许禁用超级管理员
        if user.is_superuser and not is_active:
            raise ValueError("不能禁用超级管理员")
        
        user.is_active = is_active
        user.updated_time = datetime.now()
        db.session.commit()
        
        # 清除Redis缓存
        try:
            delete_redis_cache('user', f'user_{username}')
            delete_redis_cache('user', 'all_users')
            logger.info(f"用户 {username} 状态已更新为: {'激活' if is_active else '禁用'}")
        except Exception as e:
            logger.error(f"清除用户Redis缓存失败: {e}")
    
    @staticmethod
    def get_all_strategy_names():
        """获取所有可用的策略名称"""
        strategies = StrategyPosition.query.all()
        return [s.strategy_name for s in strategies]
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户信息（包括非激活用户）"""
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        
        # 获取用户的策略信息
        user_strategies = UserStrategy.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        
        strategies_list = [us.strategy_name for us in user_strategies]
        
        return {
            'id': user.id,
            'username': user.username,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'created_time': user.created_time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login_time': user.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_time else '从未登录',
            'last_activity_time': user.last_activity_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_activity_time else '无活跃记录',
            'login_count': user.login_count,
            'has_private_key': bool(user.private_key),
            'has_public_key': bool(user.public_key),
            'strategies': strategies_list,
            'strategy_count': len(strategies_list)
        }
    
    @staticmethod
    def get_all_users_for_superuser():
        """获取所有用户列表（包括非活跃用户，仅超级管理员可查看）"""
        # MySQL 兼容的排序语法，使用 ISNULL 函数将 NULL 值排到最后
        users = User.query.order_by(
            User.is_active.desc(),  # 活跃用户排在前面
            db.text('ISNULL(last_activity_time), last_activity_time DESC'),
            db.text('ISNULL(last_login_time), last_login_time DESC')
        ).all()
        
        result = []
        for user in users:
            # 获取用户的策略信息
            user_strategies = UserStrategy.query.filter_by(
                user_id=user.id,
                is_active=True
            ).all()
            
            strategies_list = [us.strategy_name for us in user_strategies]
            
            user_info = {
                'id': user.id,
                'username': user.username,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'created_time': user.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login_time': user.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_time else '从未登录',
                'last_activity_time': user.last_activity_time.strftime('%Y-%m-%d %H:%M:%S') if user.last_activity_time else '无活跃记录',
                'login_count': user.login_count,
                'has_private_key': bool(user.private_key),
                'has_public_key': bool(user.public_key),
                'strategies': strategies_list,
                'strategy_count': len(strategies_list)
            }
            result.append(user_info)
        
        return result
    
    @staticmethod
    def change_password(username, old_password, new_password):
        """修改用户密码"""
        user = User.query.filter_by(username=username, is_active=True).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 验证旧密码
        old_password_hash = User.hash_password(old_password)
        if user.password_hash != old_password_hash:
            raise ValueError("原密码错误")
        
        # 设置新密码
        user.password_hash = User.hash_password(new_password)
        user.updated_time = datetime.now()
        db.session.commit()
        
        # 清除Redis缓存
        try:
            delete_redis_cache('user', f'user_{username}')
            logger.info(f"用户 {username} 的密码已更新")
        except Exception as e:
            logger.error(f"清除用户Redis缓存失败: {e}")
    
    @staticmethod
    def create_default_superuser():
        """创建默认超级管理员"""
        try:
            existing_superuser = User.query.filter_by(is_superuser=True).first()
            if not existing_superuser:
                User.create_user(
                    username='admin',
                    password='admin123',
                    is_superuser=True
                )
                logger.info("默认超级管理员 'admin' 已创建，密码: admin123")
                return True
            else:
                logger.info(f"超级管理员已存在: {existing_superuser.username}")
                return False
        except Exception as e:
            logger.error(f"创建默认超级管理员失败: {e}")
            return False


# 内部密码管理功能已整合到 User 类中
# 使用管理员用户的密码作为内部API密码

class InternalPasswordManager:
    """内部密码管理器 - 使用管理员用户的密码"""
    
    @staticmethod
    def get_admin_user():
        """获取管理员用户"""
        return User.query.filter_by(is_superuser=True, is_active=True).first()
    
    @staticmethod
    def verify_password(password):
        """验证内部密码（使用管理员密码）"""
        admin_user = InternalPasswordManager.get_admin_user()
        if not admin_user:
            # 如果没有管理员用户，使用默认密码 "admin123"
            default_hash = User.hash_password("admin123")
            password_hash = User.hash_password(password)
            return password_hash == default_hash
        
        # 使用管理员密码验证
        password_hash = User.hash_password(password)
        return admin_user.password_hash == password_hash
    
    @staticmethod
    def set_password(current_password, new_password):
        """设置内部密码（修改管理员密码）"""
        # 先验证当前密码
        if not InternalPasswordManager.verify_password(current_password):
            raise ValueError("当前密码验证失败")
        
        admin_user = InternalPasswordManager.get_admin_user()
        if not admin_user:
            raise ValueError("未找到管理员用户")
        
        # 更新管理员密码
        User.change_password(admin_user.username, current_password, new_password)
        
        # 清除Redis缓存
        try:
            delete_redis_cache('password', 'current_info')
            logger.info("管理员密码更新后已清除Redis缓存")
        except Exception as e:
            logger.error(f"清除密码Redis缓存失败: {e}")
    
    @staticmethod
    def get_current_password_info():
        """获取当前密码信息（不包含密码本身）"""
        # 先尝试从Redis获取
        cached_data = get_redis_cache('password', 'current_info')
        if cached_data:
            logger.debug("从Redis缓存获取密码信息")
            return cached_data
        
        # Redis中没有，从数据库获取
        admin_user = InternalPasswordManager.get_admin_user()
        if admin_user:
            result = {
                'has_password': True,
                'admin_username': admin_user.username,
                'created_time': admin_user.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_time': admin_user.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login_time': admin_user.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if admin_user.last_login_time else '从未登录',
                'message': '使用管理员用户密码作为内部API密码'
            }
        else:
            result = {
                'has_password': False,
                'default_password': 'admin123',
                'message': '未找到管理员用户，使用默认密码'
            }
        
        # 存入Redis缓存
        try:
            set_redis_cache('password', 'current_info', result)
            logger.debug("密码信息已缓存到Redis")
        except Exception as e:
            logger.error(f"缓存密码信息到Redis失败: {e}")
        
        return result
