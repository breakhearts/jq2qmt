# -*- coding: utf-8 -*-
"""
Mini QMT Trade 运行配置
根据不同需求定制运行参数
"""

# 运行配置预设
PRESETS = {
    # 开发测试配置
    'development': {
        'is_simulation': True,
        'strategy_names': ['hand_strategy'],
        'sync_interval': 10,  # 10秒同步间隔
        'enable_redis': True,
        'log_level': 'DEBUG'
    },
    
    # 生产环境配置
    'production': {
        'is_simulation': False,
        'strategy_names': None,  # 同步所有策略
        'sync_interval': 5,  # 5秒同步间隔
        'enable_redis': True,
        'log_level': 'INFO'
    },
    
    # 模拟环境配置
    'simulation': {
        'is_simulation': True,
        'strategy_names': None,  # 同步所有策略
        'sync_interval': 5,
        'enable_redis': True,
        'log_level': 'INFO'
    },
    
    # 单策略测试配置
    'single_strategy': {
        'is_simulation': True,
        'strategy_names': ['hand_strategy'],
        'sync_interval': 15,
        'enable_redis': True,
        'log_level': 'DEBUG'
    }
}

# 默认配置
DEFAULT_CONFIG = PRESETS['development']

def get_config(preset_name=None):
    """获取指定预设的配置"""
    if preset_name and preset_name in PRESETS:
        return PRESETS[preset_name].copy()
    return DEFAULT_CONFIG.copy()

def list_presets():
    """列出所有可用的预设"""
    print("可用的配置预设:")
    for name, config in PRESETS.items():
        env = "模拟" if config['is_simulation'] else "实盘"
        strategies = config['strategy_names'] or "所有策略"
        redis_status = "启用" if config['enable_redis'] else "禁用"
        print(f"  {name:15} - {env} | 策略: {strategies} | Redis: {redis_status}")

if __name__ == "__main__":
    list_presets()
