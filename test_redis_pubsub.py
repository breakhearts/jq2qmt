#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis Pub/Sub 功能测试脚本
用于测试QMT交易脚本的Redis订阅功能
"""

import redis
import json
import time
import threading
from datetime import datetime

# Redis配置（与QMT脚本保持一致）
REDIS_CONFIG = {
    'HOST': '182.92.240.95',
    'PORT': 5001,
    'DB': 1,
    'PASSWORD': 'Lemo@1995',
    'CACHE_PREFIX': 'jq_qmt:',
    'CHANNELS': {
       'POSITION_UPDATE': 'jq_qmt:position_update',
        'STRATEGY_UPDATE': 'jq_qmt:strategy_update',
        'TOTAL_POSITIONS_UPDATE': 'jq_qmt:total_positions_update',
    }
}

def test_redis_connection():
    """测试Redis连接"""
    try:
        client = redis.Redis(
            host=REDIS_CONFIG['HOST'],
            port=REDIS_CONFIG['PORT'],
            db=REDIS_CONFIG['DB'],
            password=REDIS_CONFIG['PASSWORD'],
            decode_responses=True
        )
        
        client.ping()
        print(f"✓ Redis连接成功: {REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}")
        return client
        
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return None

def publish_test_messages(client):
    """发布测试消息"""
    print("\n=== 发布测试消息 ===")
    
    # 测试持仓更新消息
    position_message = {
        'action': 'position_update',
        'strategy_name': 'hand_strategy',
        'strategy_names': ['hand_strategy'],
        'positions_count': 5,
        'update_time': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp()
    }
    
    try:
        client.publish(
            REDIS_CONFIG['CHANNELS']['POSITION_UPDATE'],
            json.dumps(position_message)
        )
        print(f"✓ 发布持仓更新消息: {position_message['strategy_name']}")
    except Exception as e:
        print(f"✗ 发布持仓更新消息失败: {e}")
    
    time.sleep(1)
    
    # 测试策略更新消息
    strategy_message = {
        'action': 'update',
        'strategy_name': 'hand_strategy',
        'update_time': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp()
    }
    
    try:
        client.publish(
            REDIS_CONFIG['CHANNELS']['STRATEGY_UPDATE'],
            json.dumps(strategy_message)
        )
        print(f"✓ 发布策略更新消息: {strategy_message['strategy_name']}")
    except Exception as e:
        print(f"✗ 发布策略更新消息失败: {e}")

def subscribe_test_messages(client):
    """订阅测试消息"""
    print("\n=== 开始订阅消息 ===")
    
    try:
        pubsub = client.pubsub()
        pubsub.subscribe([
            REDIS_CONFIG['CHANNELS']['POSITION_UPDATE'],
            REDIS_CONFIG['CHANNELS']['STRATEGY_UPDATE']
        ])
        
        print(f"已订阅频道: {list(REDIS_CONFIG['CHANNELS'].values())}")
        print("等待消息...")
        
        message_count = 0
        for message in pubsub.listen():
            if message['type'] == 'message':
                message_count += 1
                try:
                    data = json.loads(message['data'])
                    print(data)
                    print(f"\n[消息 {message_count}] 频道: {message['channel']}")
                    print(f"内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 收到2条消息后退出
                    # if message_count >= 2:
                    #     break
                        
                except json.JSONDecodeError as e:
                    print(f"解析消息失败: {e}")
                    
    except Exception as e:
        print(f"订阅消息失败: {e}")
    finally:
        if 'pubsub' in locals():
            pubsub.close()

def test_cache_operations(client):
    """测试缓存操作"""
    print("\n=== 测试缓存操作 ===")
    
    cache_key = "jq_qmt:test:cache_test"
    test_data = {
        'strategy_name': 'test_strategy',
        'positions': [
            {'code': '000001.SZ', 'volume': 1000, 'cost': 10.5},
            {'code': '600000.SH', 'volume': 500, 'cost': 8.2}
        ],
        'update_time': datetime.now().isoformat()
    }
    
    try:
        # 设置缓存
        client.setex(cache_key, 60, json.dumps(test_data, default=str))
        print(f"✓ 设置缓存: {cache_key}")
        
        # 读取缓存
        cached_data = client.get(cache_key)
        if cached_data:
            parsed_data = json.loads(cached_data)
            print(f"✓ 读取缓存成功: {len(parsed_data['positions'])} 个持仓")
        else:
            print("✗ 读取缓存失败")
            
        # 删除缓存
        client.delete(cache_key)
        print(f"✓ 删除缓存: {cache_key}")
        
    except Exception as e:
        print(f"✗ 缓存操作失败: {e}")

def main():
    print("=== Redis Pub/Sub 功能测试 ===")
    
    # 测试连接
    client = test_redis_connection()
    if not client:
        return
    
    # 测试缓存操作
    test_cache_operations(client)
    
    # 启动订阅线程
    def subscriber_thread():
        subscribe_test_messages(client)
    
    thread = threading.Thread(target=subscriber_thread, daemon=True)
    thread.start()
    
    # 等待订阅启动
    time.sleep(2)
    
    # 发布测试消息
    publish_test_messages(client)
    
    # 等待消息处理
    thread.join(timeout=500)
    
    print("\n=== 测试完成 ===")
    print("\n如果您看到了消息接收的输出，说明Redis pub/sub功能正常工作。")
    print("QMT交易脚本将能够：")
    print("1. 通过Redis订阅实时接收持仓更新通知")
    print("2. 减少HTTP请求频率，提高性能")
    print("3. 在Redis不可用时自动降级到HTTP轮询模式")

if __name__ == "__main__":
    main()
