#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据库检查和初始化脚本
仅使用Flask-SQLAlchemy进行初始化
"""

import os
import sys
from sqlalchemy import inspect

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_dependencies():
    """检查必要的依赖包"""
    missing_deps = []
    
    try:
        import flask
    except ImportError:
        missing_deps.append('flask')
    
    try:
        import flask_sqlalchemy
    except ImportError:
        missing_deps.append('flask-sqlalchemy')
    
    try:
        import pymysql
    except ImportError:
        missing_deps.append('pymysql')
    
    if missing_deps:
        print("❌ 缺少依赖包:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

def init_database():
    """初始化数据库"""
    try:
        from flask import Flask
        from src.models.models import db, StrategyPosition, InternalPassword
        from src.config import SQLALCHEMY_DATABASE_URI
        
        print("=" * 50)
        print("JQ-QMT 数据库初始化")
        print("=" * 50)
        
        # 创建Flask应用
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 初始化数据库扩展
        db.init_app(app)
        
        with app.app_context():
            print("\n1. 创建数据库表...")
            
            # 创建所有表
            db.create_all()
            print("✓ 数据库表创建成功")
            
            # 检查表是否创建成功
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ 已创建的表: {', '.join(tables)}")
            
            print("\n2. 初始化默认数据...")
            
            # 设置默认密码
            if not InternalPassword.query.first():
                InternalPassword.set_password("admin123")
                print("✓ 默认内部密码设置成功: admin123")
            else:
                print("✓ 内部密码已存在")
            
            # 创建示例策略
            if not StrategyPosition.query.filter_by(strategy_name='example_strategy').first():
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
                print("✓ 示例策略创建成功: example_strategy")
            else:
                print("✓ 示例策略已存在")
            
            # 创建手工策略示例
            if not StrategyPosition.query.filter_by(strategy_name='hand_strategy').first():
                hand_positions = [
                    {
                        'code': '000002.SZ',
                        'name': '万科A',
                        'volume': 2000,
                        'cost': 15.80
                    },
                    {
                        'code': '600036.SH', 
                        'name': '招商银行',
                        'volume': 1500,
                        'cost': 45.20
                    }
                ]
                
                StrategyPosition.update_positions('hand_strategy', hand_positions)
                print("✓ 手工策略创建成功: hand_strategy")
            else:
                print("✓ 手工策略已存在")
            
            print("\n3. 验证数据...")
            
            # 验证数据
            strategy_count = StrategyPosition.query.count()
            password_count = InternalPassword.query.count()
            
            print(f"✓ 策略数量: {strategy_count}")
            print(f"✓ 密码记录: {password_count}")
            
            # 测试密码验证
            if InternalPassword.verify_password("admin123"):
                print("✓ 默认密码验证成功")
            
            print("\n" + "=" * 50)
            print("✅ 数据库初始化完成！")
            print("=" * 50)
            
            return True
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请检查项目配置和依赖包是否正确安装")
        return False
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False

def show_usage_info():
    """显示使用说明"""
    print("\n📋 使用说明:")
    print("=" * 50)
    
    print("\n🔑 默认密码:")
    print("• 内部API密码: admin123")
    print("• 可通过 /password 页面修改")
    
    print("\n📊 示例策略:")
    print("• example_strategy: 平安银行、浦发银行")
    print("• hand_strategy: 万科A、招商银行")
    
    print("\n🚀 启动应用:")
    print("• python src/app.py")
    print("• 访问: http://localhost:5366")
    
    print("\n🔗 API接口:")
    print("• GET  /api/v1/positions/total - 获取总持仓")
    print("• POST /api/v1/positions/update - 更新持仓（需要认证）")
    print("• POST /api/v1/positions/update/internal - 内部更新接口")
    
    print("\n📄 管理页面:")
    print("• / - 主页")
    print("• /adjustment - 调整页面") 
    print("• /password - 密码管理")

def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 初始化数据库
    if init_database():
        show_usage_info()
        return True
    else:
        print("\n❌ 数据库初始化失败")
        print("\n备用方案:")
        print("1. 手动执行 database_schema.sql 文件")
        print("2. 检查数据库连接配置 (src/config.py)")
        print("3. 确保MySQL服务正常运行")
        return False

if __name__ == "__main__":
    success = main()
    
    print(f"\n按任意键退出...")
    try:
        input()
    except:
        pass
    
    sys.exit(0 if success else 1)
