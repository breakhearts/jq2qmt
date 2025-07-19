# Mini QMT Trade - Redis订阅模式独立运行脚本

## 概述
Mini QMT Trade 是基于原有QMT交易脚本改进的独立运行版本，支持Redis Pub/Sub订阅模式，可以大幅提升性能并减少HTTP请求频率。

## 主要特性

### 🚀 Redis Pub/Sub支持
- **事件驱动同步**: 收到Redis消息通知立即执行同步
- **智能缓存**: 30秒本地缓存，避免重复HTTP请求
- **自动降级**: Redis不可用时自动切换到HTTP轮询模式
- **双重保障**: 消息通知 + 定时轮询确保数据同步

### 📊 运行模式
- **守护进程模式**: 持续运行，自动同步持仓
- **单次同步模式**: 执行一次同步后退出
- **测试模式**: 测试连接和配置

### 🛠 灵活配置
- **环境选择**: 支持实盘/模拟环境
- **策略筛选**: 可指定特定策略或同步所有策略
- **参数调整**: 可自定义同步间隔、缓存时间等

## 快速开始

### 1. 检查依赖
确保已安装所需的Python包：
```bash
pip install redis requests xtquant
```

### 2. 配置检查
检查 `src/config.py` 中的配置：
- Mini QMT路径配置
- Redis连接配置
- API服务配置

### 3. 启动方式

#### 方式一：使用批处理文件 (推荐)
双击运行 `start_mini_qmt.bat`，根据提示选择运行模式。

#### 方式二：命令行启动
```bash
# 实盘模式运行
python run_mini_qmt_trade.py

# 模拟环境运行
python run_mini_qmt_trade.py --simulation

# 指定策略运行
python run_mini_qmt_trade.py --simulation --strategies hand_strategy

# 测试Redis连接
python run_mini_qmt_trade.py --test-redis

# 单次同步测试
python run_mini_qmt_trade.py --sync-once --simulation
```

#### 方式三：直接运行脚本
```bash
python src/api/mini_qmt_jq_trade.py
```

## 运行模式详解

### Redis Pub/Sub模式 (推荐)
- ✅ Redis连接成功时自动启用
- 🔄 15秒定时轮询 + 消息触发同步
- 📉 HTTP请求减少70-80%
- 🚀 响应速度更快

```
=== 初始化Redis连接 ===
Redis连接成功: 
已订阅Redis频道: ['jq_qmt:position_update', 'jq_qmt:strategy_update']
Redis pub/sub监听器已启动
✓ Redis pub/sub模式已启用，将减少HTTP请求频率
```

### HTTP轮询模式 (备用)
- ❌ Redis连接失败时自动降级
- 🔄 5秒固定轮询间隔
- 📈 保持原有HTTP请求频率

```
Redis初始化失败: [Errno 10061] 由于目标计算机积极拒绝，无法连接。
将使用HTTP轮询模式
```

## 配置选项

### 环境配置
```python
# 在 mini_qmt_config.py 中预设不同场景的配置
PRESETS = {
    'development': {    # 开发测试
        'is_simulation': True,
        'strategy_names': ['hand_strategy'],
        'sync_interval': 10
    },
    'production': {     # 生产环境
        'is_simulation': False,
        'strategy_names': None,
        'sync_interval': 5
    }
}
```

### Mini QMT配置
```python
# 在 src/config.py 中的 MINI_QMT_CONFIG
MINI_QMT_CONFIG = {
    'PATH': r'D:\国金证券QMT交易端\userdata_mini',
    'PATH_SIMULATION': r'D:\国金QMT交易端模拟\userdata_mini',
    'ACCOUNT_ID': '123456789',
    'PRICE_OFFSET': {
        'BUY': 0.01,    # 买入价格上浮
        'SELL': -0.01,  # 卖出价格下浮
    }
}
```

## 日志输出

### 正常运行日志
```
=== Mini QMT Trade 守护进程启动 ===
Mini QMT connected successfully. Session ID: 123456
Redis pub/sub模式: 定时同步间隔15秒
执行初始持仓同步...

收到Redis消息 - 频道: jq_qmt:position_update
检测到持仓更新: 策略=['hand_strategy'], 时间=2024-07-19T14:30:00
=== 开始持仓同步 (Mini QMT - Redis pub/sub模式) ===
当前持仓: 5 只股票
目标持仓: 6 只股票
同步完成: 卖出1只，买入2只
=== 持仓同步结束 (更新时间: 2024-07-19T14:30:00) ===
```

### Redis降级日志
```
Redis初始化失败: Connection refused
将使用HTTP轮询模式
=== 开始持仓同步 (Mini QMT - HTTP轮询模式) ===
```

## 故障排除

### 1. Mini QMT连接失败
- 检查Mini QMT是否已启动
- 确认路径配置是否正确
- 检查账户ID和类型设置

### 2. Redis连接失败
- 检查Redis服务是否运行
- 确认网络连接和防火墙设置
- 验证Redis配置信息

### 3. API请求失败
- 确认内部API服务是否运行
- 检查API地址和端口配置
- 验证网络连接

### 4. 持仓同步异常
- 检查股票代码格式
- 确认账户权限和资金状况
- 查看详细错误日志

## 安全注意事项

1. **实盘交易风险**: 在实盘环境下运行前，请务必在模拟环境中充分测试
2. **账户安全**: 妥善保管账户信息，不要在公共环境中运行
3. **监控运行**: 建议在交易时间内持续监控脚本运行状态
4. **备份配置**: 重要配置文件请做好备份

## 技术支持

如遇到问题，请检查：
1. 运行日志中的详细错误信息
2. 网络连接状态
3. 相关服务运行状态
4. 配置文件设置

## 更新日志

### v1.0.0 (2024-07-19)
- 初始版本发布
- 支持Redis Pub/Sub订阅模式
- 支持独立运行和多种启动方式
- 完整的错误处理和自动降级机制
