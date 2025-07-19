#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini QMT Trade 功能测试脚本
验证各项功能是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.config import MINI_QMT_CONFIG, REDIS_CONFIG, API_HOST, API_PORT
    from src.api.mini_qmt_jq_trade import MiniQmtTrade
    import redis
    import requests
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已安装所需依赖: pip install -r requirements.txt")
    sys.exit(1)

def test_config():
    """测试配置是否正确"""
    print("=== 配置测试 ===")
    
    # 测试Mini QMT配置
    print(f"Mini QMT路径: {MINI_QMT_CONFIG['PATH']}")
    print(f"模拟路径: {MINI_QMT_CONFIG['PATH_SIMULATION']}")
    print(f"账户ID: {MINI_QMT_CONFIG['ACCOUNT_ID']}")
    
    # 测试Redis配置
    print(f"Redis配置: {REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}")
    print(f"Redis启用: {REDIS_CONFIG.get('ENABLED', False)}")
    
    # 测试API配置
    print(f"API地址: http://{API_HOST}:{API_PORT}")
    
    print("✓ 配置加载成功\n")

def test_redis_connection():
    """测试Redis连接"""
    print("=== Redis连接测试 ===")
    
    if not REDIS_CONFIG.get('ENABLED', False):
        print("Redis未启用，跳过测试")
        return False
    
    try:
        client = redis.Redis(
            host=REDIS_CONFIG['HOST'],
            port=REDIS_CONFIG['PORT'],
            db=REDIS_CONFIG['DB'],
            password=REDIS_CONFIG['PASSWORD'],
            decode_responses=True
        )
        
        # 测试连接
        response = client.ping()
        if response:
            print(f"✓ Redis连接成功: {REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}")
            
            # 测试基本操作
            test_key = "mini_qmt:test:connection"
            client.setex(test_key, 10, "test_value")
            value = client.get(test_key)
            if value == "test_value":
                print("✓ Redis读写操作正常")
                client.delete(test_key)
                return True
            else:
                print("✗ Redis读写操作失败")
                return False
        else:
            print("✗ Redis ping失败")
            return False
            
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return False

def test_api_connection():
    """测试API连接"""
    print("\n=== API连接测试 ===")
    
    try:
        url = f"http://{API_HOST}:{API_PORT}/api/v1/positions/total"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ API连接成功: {url}")
            data = response.json()
            print(f"✓ 返回数据结构正常，持仓数量: {len(data.get('positions', []))}")
            return True
        else:
            print(f"✗ API响应异常: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"✗ API连接失败: 无法连接到 {API_HOST}:{API_PORT}")
        return False
    except Exception as e:
        print(f"✗ API测试失败: {e}")
        return False

def test_mini_qmt_trader():
    """测试Mini QMT Trader初始化"""
    print("\n=== Mini QMT Trader初始化测试 ===")
    
    try:
        # 创建trader实例（模拟模式）
        trader = MiniQmtTrade(is_simulation=True, strategy_names=['test_strategy'])
        
        print("✓ MiniQmtTrade实例创建成功")
        print(f"模拟模式: {trader.is_simulation}")
        print(f"Redis启用: {trader.redis_enabled}")
        print(f"策略筛选: {trader.strategy_names}")
        
        # 测试配置
        if trader.redis_enabled and trader.redis_client:
            print("✓ Redis客户端初始化成功")
        else:
            print("! Redis客户端未启用或初始化失败")
        
        # 清理
        trader.stop()
        print("✓ 清理完成")
        return True
        
    except Exception as e:
        print(f"✗ MiniQmtTrade初始化失败: {e}")
        return False

def test_position_data():
    """测试持仓数据获取"""
    print("\n=== 持仓数据获取测试 ===")
    
    try:
        trader = MiniQmtTrade(is_simulation=True)
        
        # 测试获取持仓数据
        position_data = trader.get_total_positions()
        
        if position_data:
            positions = position_data.get('positions', [])
            update_time = position_data.get('update_time')
            print(f"✓ 持仓数据获取成功")
            print(f"持仓数量: {len(positions)}")
            print(f"更新时间: {update_time}")
            
            # 测试缓存
            if trader.redis_enabled:
                print("测试缓存功能...")
                start_time = time.time()
                cached_data = trader.get_total_positions()
                cache_time = time.time() - start_time
                print(f"✓ 缓存读取耗时: {cache_time:.3f}秒")
            
            trader.stop()
            return True
        else:
            print("✗ 持仓数据为空")
            trader.stop()
            return False
            
    except Exception as e:
        print(f"✗ 持仓数据获取失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== Mini QMT Trade 功能测试 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {Path.cwd()}")
    print()
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("配置测试", test_config))
    test_results.append(("Redis连接", test_redis_connection))
    test_results.append(("API连接", test_api_connection))
    test_results.append(("Trader初始化", test_mini_qmt_trader))
    test_results.append(("持仓数据获取", test_position_data))
    
    # 运行测试
    passed = 0
    total = len(test_results)
    
    for test_name, test_func in test_results:
        try:
            if callable(test_func):
                result = test_func()
            else:
                test_func()  # 对于没有返回值的测试
                result = True
            
            if result:
                passed += 1
                
        except Exception as e:
            print(f"✗ {test_name}测试异常: {e}")
    
    # 总结
    print("\n" + "="*50)
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("✓ 所有功能正常，可以开始使用Mini QMT Trade")
    elif passed >= total - 1:
        print("! 大部分功能正常，建议检查失败的测试项")
    else:
        print("✗ 多项功能异常，请检查配置和环境")
    
    print("\n建议:")
    print("1. 如果Redis测试失败但不影响基本功能，会自动降级到HTTP轮询模式")
    print("2. 如果API测试失败，请确认内部API服务是否启动")
    print("3. 在实盘交易前，请务必在模拟环境中测试")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
