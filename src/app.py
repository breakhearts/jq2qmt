import os

from flask import Flask, request, jsonify, render_template
from models.models import db, StrategyPosition
from config import SQLALCHEMY_DATABASE_URI, API_HOST, API_PORT

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app
    
app = create_app()

@app.route('/api/v1/positions/update', methods=['POST'])
def update_positions():
    try:
        data = request.get_json()
        if not data or 'strategy_name' not in data or 'positions' not in data:
            return jsonify({'error': '无效的数据格式'}), 400
            
        StrategyPosition.update_positions(data['strategy_name'], data['positions'])
        return jsonify({'message': '持仓更新成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/strategy/<strategy_name>', methods=['GET'])
def get_strategy_positions(strategy_name):
    try:
        positions = StrategyPosition.get_strategy_positions(strategy_name)
        return jsonify({
            'positions': [{
                'code': position['code'],  # Changed from p.stock_code
                'volume': position['volume'],  # Changed from p.volume
                'cost': position['cost'],  # Changed from p.cost
                'update_time': position['update_time'].strftime('%Y-%m-%d %H:%M:%S')
            } for position in positions]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/positions/total', methods=['GET'])
def get_total_positions():
    try:
        # 从查询参数获取策略名列表，使用逗号分隔
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