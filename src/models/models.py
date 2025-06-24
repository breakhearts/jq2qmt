from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
import hashlib

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
    def get_total_positions(strategy_names=None, include_adjustments=True):
        # 获取策略数据
        if strategy_names:
            all_strategies = StrategyPosition.query.filter(
                StrategyPosition.strategy_name.in_(strategy_names)
            ).all()
        else:
            # 获取所有策略，但可以选择是否包含调整策略
            if include_adjustments:
                all_strategies = StrategyPosition.query.all()
            else:
                all_strategies = StrategyPosition.query.filter(
                    ~StrategyPosition.strategy_name.like('ADJUSTMENT_%')
                ).all()
            
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
                        'name': pos.get('name', code),  # 使用股票名称，如果没有则使用代码
                        'total_volume': 0,
                        'total_cost': 0
                    }
                
                # 对于调整策略，直接加减持仓数量和成本
                if strategy.strategy_name.startswith('ADJUSTMENT_'):
                    total_positions[code]['total_volume'] += pos['volume']
                    total_positions[code]['total_cost'] += pos['volume'] * pos['cost']
                else:
                    total_positions[code]['total_volume'] += pos['volume']
                    total_positions[code]['total_cost'] += pos['volume'] * pos['cost']
        
        # 计算平均成本并过滤掉持仓为0的股票
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


class InternalPassword(db.Model):
    __tablename__ = 'internal_passwords'
    
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(64), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.now)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    @staticmethod
    def hash_password(password):
        """对密码进行SHA256哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    @staticmethod
    def set_password(password):
        """设置或更新密码"""
        password_hash = InternalPassword.hash_password(password)
        
        # 查找现有记录
        existing = InternalPassword.query.first()
        if existing:
            existing.password_hash = password_hash
            existing.updated_time = datetime.now()
        else:
            # 创建新记录
            new_password = InternalPassword(password_hash=password_hash)
            db.session.add(new_password)
        
        db.session.commit()
    
    @staticmethod
    def verify_password(password):
        """验证密码"""
        password_hash = InternalPassword.hash_password(password)
        existing = InternalPassword.query.first()
        
        if not existing:
            # 如果没有设置密码，使用默认密码 "admin123"
            default_hash = InternalPassword.hash_password("admin123")
            return password_hash == default_hash
        
        return existing.password_hash == password_hash
    
    @staticmethod
    def get_current_password_info():
        """获取当前密码信息（不包含密码本身）"""
        existing = InternalPassword.query.first()
        if existing:
            return {
                'has_password': True,
                'created_time': existing.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_time': existing.updated_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            return {
                'has_password': False,
                'default_password': 'admin123',
                'message': '使用默认密码，建议通过数据库修改'
            }
