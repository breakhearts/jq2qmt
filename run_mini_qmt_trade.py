#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini QMT Trade 启动脚本
支持不同的运行模式和配置选项
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.api.mini_qmt_jq_trade import MiniQmtTrade

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Mini QMT Trade 交易脚本')
    
    parser.add_argument(
        '--simulation',
        action='store_true',
        help='使用模拟环境 (默认: False, 使用实盘环境)'
    )
    
    parser.add_argument(
        '--strategies',
        type=str,
        nargs='+',
        help='指定要同步的策略名称 (例如: --strategies hand_strategy auto_strategy)'
    )
    
    parser.add_argument(
        '--test-redis',
        action='store_true',
        help='测试Redis连接后退出'
    )
    
    parser.add_argument(
        '--sync-once',
        action='store_true',
        help='执行一次同步后退出'
    )
    
    return parser.parse_args()

def test_redis_connection():
    """测试Redis连接"""
    print("=== Redis连接测试 ===")
    try:
        trader = MiniQmtTrade()
        if trader.redis_enabled and trader.redis_client:
            print("✓ Redis连接正常")
            print(f"Redis配置: {trader.redis_client.connection_pool.connection_kwargs}")
            return True
        else:
            print("✗ Redis未启用或连接失败")
            return False
    except Exception as e:
        print(f"✗ Redis连接测试失败: {e}")
        return False

def main():
    """主函数"""
    args = parse_args()
    
    print("=== Mini QMT Trade 启动器 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"项目根目录: {project_root}")
    
    # Redis连接测试
    if args.test_redis:
        success = test_redis_connection()
        sys.exit(0 if success else 1)
    
    # 创建交易实例
    print(f"\n创建交易实例...")
    print(f"环境: {'模拟' if args.simulation else '实盘'}")
    if args.strategies:
        print(f"指定策略: {args.strategies}")
    else:
        print("策略: 所有策略")
    
    try:
        trader = MiniQmtTrade(
            is_simulation=args.simulation,
            strategy_names=args.strategies
        )
        
        # 连接QMT
        print("\n连接Mini QMT...")
        trader.connect()
        
        if args.sync_once:
            # 单次同步模式
            print("\n执行单次同步...")
            trader.sync_positions()
            print("单次同步完成，程序退出")
        else:
            # 守护进程模式
            print("\n启动守护进程模式...")
            print("按 Ctrl+C 停止程序\n")
            trader.run_daemon()
            
    except KeyboardInterrupt:
        print("\n收到停止信号，正在退出...")
    except Exception as e:
        print(f"\n程序异常: {e}")
        sys.exit(1)
    finally:
        print("程序已退出")

if __name__ == "__main__":
    main()
