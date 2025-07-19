# QMT Redis Pub/Sub 集成说明

## 概述
QMT交易脚本现已集成Redis发布/订阅功能，可以大幅降低HTTP请求消耗，提高系统性能。

## 主要改进

### 🚀 性能提升
- **减少HTTP请求**：从每5秒轮询改为事件驱动同步
- **智能缓存**：30秒本地缓存，避免重复请求  
- **自动降级**：Redis不可用时自动切换到HTTP轮询模式

### 📡 Redis Pub/Sub 机制
- **服务器端**：数据更新时发布Redis消息
- **QMT端**：订阅Redis消息，收到通知立即同步
- **双重保障**：消息通知 + 定时轮询（15秒间隔）

## 快速开始

### 1. 确保Redis服务运行
检查config.py中的Redis配置：
```python
REDIS_CONFIG = {
    'ENABLED': True,
    'HOST': 'xxx.xxx.xxx.xxx',
    'PORT': 5001,
    'DB': 1,
    'PASSWORD': 'TEST_PASSWORD',
}
```

### 2. 安装依赖
```bash
pip install redis==5.0.1
```

### 3. 运行QMT脚本
在QMT中加载 `qmt_jq_trade` 脚本，观察启动日志：

```
=== 初始化Redis连接 ===
Redis连接成功: XXX.XXX.XXX.XXX
已订阅Redis频道: ['jq_qmt:position_update', 'jq_qmt:strategy_update']
Redis pub/sub监听器已启动
✓ Redis pub/sub模式已启用，将减少HTTP请求频率
```

### 4. 测试功能
运行测试脚本验证pub/sub功能：
```bash
python test_redis_pubsub.py
```

## 工作模式

### Redis Pub/Sub 模式（推荐）
- ✅ Redis连接成功
- ✅ 订阅消息通知
- 🔄 15秒定时轮询 + 消息触发同步
- 📉 HTTP请求减少70-80%

### HTTP轮询模式（备用）
- ❌ Redis连接失败或未启用
- 🔄 5秒固定轮询
- 📈 保持原有HTTP请求频率

## 消息格式

### 持仓更新通知
```json
{
  "action": "position_update",
  "strategy_name": "hand_strategy",
  "strategy_names": ["hand_strategy"],
  "update_time": "2024-07-19T14:30:00"
}
```

### 策略更新通知
```json
{
  "action": "update",
  "strategy_name": "hand_strategy", 
  "update_time": "2024-07-19T14:30:00"
}
```

## 日志示例

### 正常运行日志
```
Redis pub/sub模式: 数据未更新，跳过同步
使用缓存的持仓数据 (缓存时间: 12.3秒)
收到Redis消息 - 频道: jq_qmt:position_update
检测到持仓更新: 策略=['hand_strategy'], 时间=2024-07-19T14:30:00
=== 开始持仓同步 (模式: Redis pub/sub) ===
```

### 降级模式日志
```
Redis连接失败: Connection refused
! Redis连接失败，使用HTTP轮询模式
从服务器获取持仓数据成功 (策略: ['hand_strategy'])
=== 开始持仓同步 (模式: HTTP轮询) ===
```

## 故障排除

### 常见问题

1. **Redis连接失败**
   - 检查Redis服务器是否运行
   - 验证config.py中的连接参数
   - 确认网络连接和防火墙设置

2. **消息接收异常**
   - 检查频道订阅是否成功
   - 验证消息格式是否正确
   - 查看Redis服务器日志

3. **性能无明显提升**
   - 确认Redis pub/sub模式已启用
   - 检查缓存命中率
   - 对比HTTP请求频率

### 调试模式
在脚本中设置：
```python
DEBUG = True  # 启用调试模式
```

## 注意事项

1. **兼容性**：保持向后兼容，Redis不可用时自动降级
2. **数据一致性**：消息通知可能有秒级延迟
3. **资源使用**：Redis连接和线程会占用少量系统资源
4. **网络要求**：需要稳定的Redis服务器连接

## 技术实现

### 关键组件
- `init_redis_connection()` - Redis连接初始化
- `start_redis_subscriber()` - 启动消息订阅
- `redis_message_listener()` - 消息监听线程
- `QMTAPI.get_total_positions()` - 智能缓存机制

### 线程安全
- 使用daemon线程处理Redis监听
- 线程间通过全局变量通信
- 异常处理确保主程序稳定

---
**更多详细信息请参考 REDIS_README.md**
