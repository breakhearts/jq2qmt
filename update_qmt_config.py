#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT交易脚本配置更新工具
自动更新qmt_jq_trade文件中的API URL和Redis配置
"""

import os
import re
from datetime import datetime

def update_qmt_trade_config(api_host='127.0.0.1', api_port=5366):
    """更新QMT交易脚本中的配置"""
    
    qmt_trade_file = os.path.join('src', 'api', 'qmt_jq_trade')
    
    if not os.path.exists(qmt_trade_file):
        print(f"错误：找不到文件 {qmt_trade_file}")
        return False
    
    try:
        # 读取文件内容
        with open(qmt_trade_file, 'r', encoding='gbk') as f:
            content = f.read()
        
        # 更新API URL
        new_api_url = f"http://{api_host}:{api_port}"
        content = re.sub(
            r'API_URL = "http://[^"]*"',
            f'API_URL = "{new_api_url}"',
            content
        )
        
        # 更新Redis配置（从config.py读取）
        try:
            from src.config import REDIS_CONFIG, API_HOST, API_PORT
            
            # 使用config.py中的配置更新
            if API_HOST and API_PORT:
                config_api_url = f"http://{API_HOST}:{API_PORT}"
                content = re.sub(
                    r'API_URL = "http://[^"]*"',
                    f'API_URL = "{config_api_url}"',
                    content
                )
                print(f"✓ API URL更新为: {config_api_url}")
            
            # 更新Redis配置
            redis_config_str = f"""REDIS_CONFIG = {{
    'ENABLED': {REDIS_CONFIG.get('ENABLED', True)},
    'HOST': '{REDIS_CONFIG.get('HOST', 'localhost')}',
    'PORT': {REDIS_CONFIG.get('PORT', 6379)},
    'DB': {REDIS_CONFIG.get('DB', 0)},
    'PASSWORD': '{REDIS_CONFIG.get('PASSWORD', '')}',
    'CACHE_PREFIX': '{REDIS_CONFIG.get('CACHE_PREFIX', 'jq_qmt:')}',
    'CHANNELS': {{
        'POSITION_UPDATE': 'jq_qmt:position_update',  # 持仓更新通知
        'STRATEGY_UPDATE': 'jq_qmt:strategy_update',  # 策略更新通知
        'TOTAL_POSITIONS_UPDATE': 'jq_qmt:total_positions_update',  # 总持仓更新通知

    }}
}}"""
            
            # 替换Redis配置
            pattern = r"REDIS_CONFIG = \{[^}]*(?:\{[^}]*\}[^}]*)*\}"
            content = re.sub(pattern, redis_config_str, content, flags=re.MULTILINE | re.DOTALL)
            print("✓ Redis配置已同步")
            
        except ImportError as e:
            print(f"警告：无法导入配置文件，使用默认配置: {e}")
            print(f"✓ API URL更新为: {new_api_url}")
        
        # 备份原文件
        backup_file = f"{qmt_trade_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w', encoding='gbk') as f:
            # 读取原文件重新写入备份
            with open(qmt_trade_file, 'r', encoding='gbk') as orig:
                f.write(orig.read())
        
        # 写入更新后的内容
        with open(qmt_trade_file, 'w', encoding='gbk') as f:
            f.write(content)
        
        print(f"✓ 配置更新完成")
        print(f"✓ 原文件已备份为: {backup_file}")
        return True
        
    except Exception as e:
        print(f"错误：更新配置失败 - {e}")
        return False

def verify_redis_pubsub_integration():
    """验证Redis pub/sub集成"""
    print("\n=== 验证Redis Pub/Sub集成 ===")
    
    qmt_trade_file = os.path.join('src', 'api', 'qmt_jq_trade')
    
    if not os.path.exists(qmt_trade_file):
        print(f"错误：找不到文件 {qmt_trade_file}")
        return False
    
    try:
        with open(qmt_trade_file, 'r', encoding='gbk') as f:
            content = f.read()
        
        # 检查关键功能
        checks = [
            ('import redis', 'Redis模块导入'),
            ('init_redis_connection', 'Redis连接初始化函数'),
            ('start_redis_subscriber', 'Redis订阅启动函数'),
            ('redis_message_listener', 'Redis消息监听函数'),
            ('REDIS_CONFIG', 'Redis配置'),
            ('g.use_redis_pubsub', 'Redis pub/sub模式标志'),
            ('publish_position_update_message', '持仓更新消息发布')
        ]
        
        missing_features = []
        for check, description in checks:
            if check in content:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                missing_features.append(description)
        
        if missing_features:
            print(f"\n警告：缺少以下功能: {', '.join(missing_features)}")
            return False
        else:
            print("\n✓ Redis pub/sub集成验证通过")
            return True
            
    except Exception as e:
        print(f"错误：验证失败 - {e}")
        return False

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "="*60)
    print("Redis Pub/Sub 集成使用说明")
    print("="*60)
    
    print("\n📋 功能概览:")
    print("• QMT交易脚本现已支持Redis发布/订阅模式")
    print("• 自动减少HTTP请求频率，提高性能")
    print("• Redis不可用时自动降级到HTTP轮询模式")
    
    print("\n🚀 启动步骤:")
    print("1. 确保Redis服务器正常运行")
    print("2. 检查config.py中的Redis配置")
    print("3. 运行QMT交易脚本")
    print("4. 观察日志中的Redis连接状态")
    
    print("\n💡 工作原理:")
    print("• 服务器端：数据更新时发布Redis消息")
    print("• QMT端：订阅Redis消息，收到通知后触发同步")
    print("• 缓存机制：减少重复的HTTP请求")
    
    print("\n📊 性能优化:")
    print("• Redis模式：同步间隔增加到15秒（接收到消息时立即同步）")
    print("• HTTP模式：保持原有5秒间隔")
    print("• 缓存命中：跳过不必要的网络请求")
    
    print("\n🔧 配置说明:")
    print("• REDIS_CONFIG['ENABLED']: 是否启用Redis")
    print("• g.use_redis_pubsub: Redis pub/sub模式状态")
    print("• 频道订阅: position_update, strategy_update")
    
    print("\n📝 测试方法:")
    print("• 运行: python test_redis_pubsub.py")
    print("• 观察QMT日志中的Redis连接状态")
    print("• 检查HTTP请求频率是否降低")

def main():
    print("=== QMT Redis Pub/Sub 配置更新工具 ===")
    
    # 更新配置
    if update_qmt_trade_config():
        # 验证集成
        if verify_redis_pubsub_integration():
            show_usage_instructions()
        else:
            print("\n❌ Redis pub/sub集成验证失败，请检查代码")
    else:
        print("\n❌ 配置更新失败")

if __name__ == "__main__":
    main()
