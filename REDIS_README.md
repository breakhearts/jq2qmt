# Redis缓存集成说明

本项目已集成Redis缓存功能，用于提高数据访问性能和减少数据库负载。同时支持Redis发布/订阅(pub/sub)机制，大幅降低HTTP请求消耗。

## 功能特性

### 缓存策略
- **策略持仓数据缓存**：自动缓存单个策略的持仓数据
- **所有策略数据缓存**：缓存所有策略的汇总数据
- **总持仓计算缓存**：缓存复杂的总持仓计算结果
- **密码信息缓存**：缓存系统密码配置信息

### Redis发布/订阅(Pub/Sub)功能 🆕
- **实时消息通知**：数据更新时立即通知QMT客户端
- **智能同步触发**：仅在数据变化时触发同步操作
- **HTTP请求优化**：减少70-80%的轮询请求
- **自动降级机制**：Redis不可用时自动切换到HTTP轮询

### 缓存机制
- **读取优先级**：Redis缓存 → MySQL数据库
- **写入同步**：数据更新时同时更新MySQL和Redis
- **自动失效**：缓存数据设置合理的过期时间
- **故障降级**：Redis不可用时自动降级到数据库查询

## 配置说明

### Redis配置 (config.py)
```python
REDIS_CONFIG = {
    # 是否启用 Redis 缓存
    'ENABLED': True,
    
    # Redis 连接配置
    'HOST': 'xxx.xxx.xxx.xx',    # Redis服务器地址
    'PORT': xxxx,               # Redis端口
    'DB': 1,                    # Redis数据库编号
    'PASSWORD': 'Lemo@1995',    # Redis密码
    
    # Redis 使用配置
    'CACHE_PREFIX': 'jq_qmt:',         # 缓存键前缀
    'DEFAULT_TIMEOUT': 86400,          # 默认过期时间（秒）
    
    # Pub/Sub 频道配置 🆕
    'CHANNELS': {
        'POSITION_UPDATE': 'jq_qmt:position_update',  # 持仓更新通知
        'STRATEGY_UPDATE': 'jq_qmt:strategy_update',  # 策略更新通知
    }
}
```

### 配置项说明
- `ENABLED`: 设置为 `False` 可完全禁用Redis缓存
- `HOST/PORT`: Redis服务器连接信息
- `DB`: Redis数据库编号，用于数据隔离
- `PASSWORD`: Redis认证密码（如果需要）
- `CACHE_PREFIX`: 缓存键名前缀，避免键名冲突
- `DEFAULT_TIMEOUT`: 缓存默认过期时间（24小时）

## 安装和使用

### 1. 安装Redis依赖
```bash
# 方法1：使用安装脚本
python install_redis.py

# 方法2：手动安装
pip install redis==5.0.1
```

### 2. 配置Redis服务器
确保Redis服务器正常运行，并在 `config.py` 中配置正确的连接信息。

### 3. 更新QMT配置 🆕
```bash
# 自动更新QMT交易脚本配置
python update_qmt_config.py
```

### 4. 启动应用
```bash
python src/app.py
```

### 5. 测试Redis Pub/Sub 🆕
```bash
# 测试Redis发布/订阅功能
python test_redis_pubsub.py
```

## 缓存键结构

### 策略相关缓存
- `jq_qmt:strategy:{strategy_name}` - 单个策略持仓数据
- `jq_qmt:strategy:all_strategies` - 所有策略数据
- `jq_qmt:strategy:total_positions` - 总持仓数据
- `jq_qmt:strategy:total_positions_no_adj` - 不含调整策略的总持仓

### 系统相关缓存
- `jq_qmt:password:current_info` - 当前密码配置信息

### Redis Pub/Sub 频道 🆕
- `jq_qmt:position_update` - 持仓数据更新通知
- `jq_qmt:strategy_update` - 策略数据更新通知

## Redis Pub/Sub 消息格式 🆕

### 持仓更新消息
```json
{
  "action": "position_update",
  "strategy_name": "hand_strategy",
  "strategy_names": ["hand_strategy"],
  "positions_count": 5,
  "update_time": "2024-07-19T14:30:00",
  "timestamp": 1721374200.123
}
```

### 策略更新消息
```json
{
  "action": "update",  // "update", "create", "delete"
  "strategy_name": "hand_strategy", 
  "update_time": "2024-07-19T14:30:00",
  "timestamp": 1721374200.123
}
```

## 性能优化

### Redis Pub/Sub 模式性能提升 🆕
1. **智能同步间隔**：
   - Redis模式：15秒轮询 + 消息触发立即同步
   - HTTP模式：5秒固定轮询
   - 性能提升：减少70-80%的HTTP请求

2. **消息驱动同步**：
   - 数据更新时立即通知QMT客户端
   - 避免无效的轮询请求
   - 实现近实时的数据同步

3. **智能缓存策略**：
   - 缓存命中时跳过HTTP请求
   - 消息通知时清除相关缓存
   - 30秒缓存超时机制

### 缓存命中率优化
1. **热数据优先**：常用的策略数据自动保持在缓存中
2. **智能更新**：数据更新时自动刷新相关缓存
3. **批量操作**：减少不必要的缓存更新频率

### 内存使用优化
1. **合理过期时间**：避免缓存数据无限增长
2. **键名压缩**：使用MD5哈希压缩复杂查询的键名
3. **数据结构优化**：JSON序列化时优化数据结构

## 监控和调试

### 日志记录
- Redis连接状态记录在应用日志中
- 缓存命中/未命中情况可通过日志跟踪
- 缓存更新操作有详细日志

### 调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 手动缓存管理
```python
from src.models.models import get_redis_cache, set_redis_cache, delete_redis_cache

# 获取缓存
data = get_redis_cache('strategy', 'strategy_name')

# 设置缓存
set_redis_cache('strategy', 'strategy_name', data, timeout=3600)

# 删除缓存
delete_redis_cache('strategy', 'strategy_name')
```

## 故障处理

### Redis连接失败
- **自动降级**：Redis不可用时自动使用数据库
- **错误日志**：连接失败会记录详细错误信息
- **零停机**：Redis故障不影响应用正常运行

### 缓存数据不一致
```python
# 清除所有缓存
from src.models.models import redis_client
if redis_client:
    redis_client.flushdb()
```

### 性能问题排查
1. 检查Redis服务器性能
2. 查看缓存命中率日志
3. 调整缓存过期时间
4. 优化查询条件

## 最佳实践

1. **定期监控**：观察Redis内存使用情况
2. **合理配置**：根据业务需求调整缓存时间
3. **故障预案**：确保Redis故障时应用可正常运行
4. **数据一致性**：重要数据更新后及时清理相关缓存

## 注意事项

1. Redis缓存是提高性能的手段，不是数据持久化的替代品
2. 敏感数据（如密码哈希）不会被缓存
3. 缓存数据可能存在短暂的延迟一致性问题
4. 生产环境建议配置Redis持久化和高可用
