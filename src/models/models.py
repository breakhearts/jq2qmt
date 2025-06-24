from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

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

    @staticmethod
    def get_strategy_positions(strategy_name):
        strategy = StrategyPosition.query.filter_by(strategy_name=strategy_name).first()
        return strategy.positions if strategy else []

    @staticmethod
    def get_all_strategy_positions():
        strategies = StrategyPosition.query.all()
        return [{
            'strategy_name': strategy.strategy_name,
            'positions': strategy.positions,
            'update_time': strategy.update_time
        } for strategy in strategies]

    @staticmethod
    def get_total_positions(strategy_names=None):
        # 获取策略数据
        if strategy_names:
            all_strategies = StrategyPosition.query.filter(
                StrategyPosition.strategy_name.in_(strategy_names)
            ).all()
        else:
            all_strategies = StrategyPosition.query.all()
            
        total_positions = {}
        # 设置默认的最早开始时间
        latest_update_time = datetime(1970, 1, 1)
        
        for strategy in all_strategies:
            # 更新最新时间
            if latest_update_time is None or strategy.update_time > latest_update_time:
                latest_update_time = strategy.update_time
                
            for pos in strategy.positions:
                code = pos['code']
                if code not in total_positions:
                    total_positions[code] = {
                        'code': code,
                        'name': pos.get('name', ""),  
                        'total_volume': 0,
                        'total_cost': 0
                    }
                total_positions[code]['total_volume'] += pos['volume']
                total_positions[code]['total_cost'] += pos['volume'] * pos['cost']
        
        # 计算平均成本
        for code in total_positions:
            if total_positions[code]['total_volume'] > 0:
                total_positions[code]['avg_cost'] = (
                    total_positions[code]['total_cost'] / 
                    total_positions[code]['total_volume']
                )
                del total_positions[code]['total_cost']
        
        return {
            'positions': list(total_positions.values()),
            'update_time': latest_update_time
        }
