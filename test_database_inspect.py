#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库表检查功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_table_inspection():
    """测试表检查功能"""
    try:
        from sqlalchemy import create_engine, inspect
        from src.config import SQLALCHEMY_DATABASE_URI
        
        print("正在连接数据库...")
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        
        print("正在检查表结构...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"数据库中的表: {tables}")
        
        required_tables = ['strategy_positions', 'internal_passwords', 'users']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"缺少数据表: {missing_tables}")
        else:
            print("✓ 所有必需的表都存在")
            
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("数据库表检查测试")
    print("=" * 50)
    
    success = test_table_inspection()
    
    if success:
        print("\n✅ 测试通过")
    else:
        print("\n❌ 测试失败")
