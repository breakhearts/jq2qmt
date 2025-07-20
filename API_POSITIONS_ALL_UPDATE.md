# API Redis缓存权限控制更新

## 更新说明

对 API 接口进行了 Redis 缓存权限控制的安全性增强，解决了缓存数据泄露的安全漏洞。

## 问题分析

原有的 Redis 缓存实现存在严重的安全漏洞：

1. **权限绕过**：`get_all_strategy_positions()` 从 Redis 缓存中返回所有策略数据，没有考虑用户权限
2. **数据泄露**：不同用户可能通过 Redis 缓存看到他们没有权限访问的策略数据
3. **缓存污染**：超级用户访问过的数据会被缓存，普通用户随后可能获取到这些数据

## 解决方案

采用 **"先查询MySQL权限，再按策略名查询Redis"** 的方案：

### 核心思路：
1. **先查询MySQL数据库**获取用户的权限策略列表
2. **根据策略名称查询对应的Redis缓存键**
3. **只返回用户有权限访问的数据**

### 技术实现：

#### 1. 修改 `get_all_strategy_positions()` 方法
```python
def get_all_strategy_positions(user_id=None, is_superuser=False):
    # 1. 先查询MySQL获取用户可访问的策略列表
    if is_superuser:
        all_strategies = StrategyPosition.query.all()
        allowed_strategy_names = [s.strategy_name for s in all_strategies]
    elif user_id:
        user_strategies = UserStrategy.get_user_strategies(user_id)
        allowed_strategy_names = [s['strategy_name'] for s in user_strategies]
    
    # 2. 根据策略名称查询对应的Redis缓存
    for strategy_name in allowed_strategy_names:
        cached_data = get_redis_cache('strategy', strategy_name)
        # 处理缓存数据...
```

#### 2. 修改 `get_total_positions()` 方法
```python
def get_total_positions(strategy_names=None, include_adjustments=True, user_id=None, is_superuser=False):
    # 1. 根据用户权限确定要查询的策略列表
    # 2. 按策略名称逐个查询Redis缓存
    # 3. 合并计算总持仓
```

## 缓存策略改进

### 缓存键设计：
- **按策略名称独立缓存**：`strategy:{strategy_name}`
- **不再使用复合缓存键**：避免权限交叉污染
- **5分钟缓存超时**：平衡性能与数据一致性

### 权限控制流程：
```
用户请求 → 验证身份 → 查询MySQL权限表 → 按策略名查询Redis → 返回授权数据
```

## 更新的接口

以下接口已经更新为安全的权限控制模式：

1. **`/api/v1/positions/all`** - 需要用户名密码认证
2. **`/api/v1/positions/all/web`** - 使用Web会话认证
3. **`/api/v1/positions/total`** - 需要用户名密码认证
4. **`/api/v1/positions/total/web`** - 使用Web会话认证

## 安全性改进

1. **杜绝权限绕过**：每次都先验证MySQL权限
2. **防止数据泄露**：只返回用户有权限的策略数据
3. **缓存隔离**：不同策略使用独立的缓存键
4. **审计跟踪**：保留请求计数和权限检查日志

## 性能优化

1. **按需查询**：只查询用户有权限的策略
2. **缓存复用**：相同策略的多次请求可以复用缓存
3. **并发友好**：多个用户访问不同策略不会相互影响
4. **内存高效**：避免缓存大量用户无权访问的数据

## 向后兼容性

- **API接口保持不变**：外部调用无需修改
- **响应格式一致**：返回数据结构不变
- **功能增强**：在原有功能基础上增加安全控制

## 测试建议

1. **权限测试**：验证普通用户只能看到授权策略
2. **缓存测试**：验证不同用户的缓存互不影响
3. **性能测试**：验证新方案的性能表现
4. **并发测试**：验证多用户同时访问的稳定性
