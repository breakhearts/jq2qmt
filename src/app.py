import os

from flask import Flask, request, jsonify, render_template
from models.models import db, StrategyPosition
from config import SQLALCHEMY_DATABASE_URI, API_HOST, API_PORT, CRYPTO_AUTH_CONFIG
from auth.simple_crypto_auth import SimpleCryptoAuth, require_auth
import auth.simple_crypto_auth as auth_module

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # 初始化认证系统
    init_auth_system()
    
    with app.app_context():
        db.create_all()
    
    return app

def init_auth_system():
    """初始化认证系统"""
    if CRYPTO_AUTH_CONFIG.get('ENABLED', True):
        # 启用加密认证
        private_key = CRYPTO_AUTH_CONFIG['PRIVATE_KEY']
        public_key = CRYPTO_AUTH_CONFIG['PUBLIC_KEY']
        
        # 设置全局认证实例
        auth_module.crypto_auth = SimpleCryptoAuth(private_key, public_key)
        print("加密认证系统已启用")
    else:
        # 禁用加密认证，使用简单API密钥
        print("加密认证已禁用，使用简单API密钥认证")
        if not CRYPTO_AUTH_CONFIG.get('SIMPLE_API_KEY'):
            print("警告: 未配置简单API密钥，API将不安全！")

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

@app.route('/api/v1/auth/info', methods=['GET'])
def get_auth_info():
    """获取认证系统信息"""
    return jsonify({
        'crypto_enabled': CRYPTO_AUTH_CONFIG.get('ENABLED', True),
        'auth_type': 'crypto' if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else 'simple',
        'public_key': CRYPTO_AUTH_CONFIG['PUBLIC_KEY'] if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else None,
        'algorithm': 'RSA-2048' if CRYPTO_AUTH_CONFIG.get('ENABLED', True) else 'API-Key'
    })

@app.route('/api/v1/positions/strategy/<strategy_name>', methods=['GET'])
def get_strategy_positions(strategy_name):
    try:
        positions = StrategyPosition.get_strategy_positions(strategy_name)
        return jsonify({
            'positions': [{
                'code': position['code'],
                'volume': position['volume'],
                'cost': position['cost'],
                'update_time': position['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            } for position in positions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/total', methods=['GET'])
def get_total_positions():
    try:
        strategy_names_str = request.args.get('strategies')
        strategy_names = strategy_names_str.split(',') if strategy_names_str else None
        
        result = StrategyPosition.get_total_positions(strategy_names)
        return jsonify({
            'positions': result['positions'],
            'update_time': result['update_time'].strftime('%Y-%m-%d %H:%M:%S') if result['update_time'] else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/all', methods=['GET'])
def get_all_positions():
    try:
        positions = StrategyPosition.get_all_strategy_positions()
        return jsonify({
            'strategies': [{
                'strategy_name': item['strategy_name'],
                'positions': [{
                    'code': pos['code'],
                    'volume': pos['volume'],
                    'cost': pos['cost']
                } for pos in item['positions']],
                'update_time': item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            } for item in positions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=True
    )