# 用户策略关联系统更新说明

## 概述

本次更新添加了用户-策略关联系统，用于管理用户可以查看的策略，并记录每日请求次数。

## 新增功能

### 1. 数据库表结构

新增 `user_strategies` 表：
- `id`: 主键ID
- `user_id`: 用户ID（外键关联users表）
- `strategy_name`: 策略名称
- `daily_request_count`: 当日请求次数
- `last_request_date`: 最后请求日期
- `created_time`: 创建时间
- `updated_time`: 更新时间
- `is_active`: 是否激活

### 2. 模型类

新增 `UserStrategy` 模型类，提供以下静态方法：
- `get_user_strategies(user_id)`: 获取用户可查看的策略列表
- `add_user_strategy(user_id, strategy_name)`: 为用户添加策略权限
- `remove_user_strategy(user_id, strategy_name)`: 移除用户的策略权限
- `check_user_strategy_permission(user_id, strategy_name)`: 检查用户策略权限
- `increment_request_count(user_id, strategy_names)`: 增加请求次数
- `get_user_strategy_stats(user_id)`: 获取用户策略统计信息

### 3. API接口更新

#### 3.1 更新的接口

**`/api/v1/positions/total`**
- 添加了策略权限检查
- 只有用户有权限的策略才能查看
- 每次请求会自动增加对应策略的请求次数
- 次日0点请求次数会自动清零

#### 3.2 新增的接口

**`/api/v1/user/strategies` (GET)**
- 获取当前登录用户的策略权限和统计信息
- 需要Web登录认证

**`/api/v1/admin/user/<user_id>/strategies` (GET/POST/DELETE)**
- 管理员管理用户策略权限
- GET: 获取指定用户的策略权限
- POST: 为用户添加策略权限
- DELETE: 移除用户的策略权限
- 需要超级管理员权限

### 4. 注册页面更新

注册页面新增策略选择功能：
- 用户注册时可以输入可查看的策略名称
- 每行一个策略名称
- 留空则无法查看任何策略

### 5. 每日重置任务

新增 `daily_reset_task.py` 脚本：
- 每天0点重置所有用户的策略请求次数
- 可通过crontab或Windows任务计划程序定时执行
- 提供日志记录功能

## 部署说明

### 1. 数据库更新

执行以下SQL语句创建新表：

```sql
CREATE TABLE IF NOT EXISTS `user_strategies` (
    `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id` int(11) NOT NULL COMMENT '用户ID',
    `strategy_name` varchar(100) NOT NULL COMMENT '策略名称',
    `daily_request_count` int(11) NOT NULL DEFAULT 0 COMMENT '当日请求次数',
    `last_request_date` date DEFAULT NULL COMMENT '最后请求日期',
    `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否激活',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_user_strategy` (`user_id`, `strategy_name`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_strategy_name` (`strategy_name`),
    KEY `idx_last_request_date` (`last_request_date`),
    KEY `idx_is_active` (`is_active`),
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户策略关联表';
```

或者直接执行更新后的 `database_schema.sql` 文件。

### 2. 配置定时任务

#### Linux/macOS (crontab)

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天0点1分执行）
1 0 * * * /usr/bin/python3 /path/to/jq2qmt/daily_reset_task.py >> /path/to/logs/daily_reset.log 2>&1
```

#### Windows (任务计划程序)

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器为"每天"，时间为"00:01"
4. 操作选择"启动程序"
5. 程序路径：`python.exe`
6. 参数：`daily_reset_task.py`
7. 起始位置：项目根目录

### 3. 权限配置

#### 为现有用户添加策略权限

可以通过以下方式为现有用户添加策略权限：

1. **通过API接口（推荐）**：
   使用管理员账户调用 `/api/v1/admin/user/<user_id>/strategies` 接口

2. **直接操作数据库**：
   ```sql
   INSERT INTO user_strategies (user_id, strategy_name) VALUES (用户ID, '策略名称');
   ```

3. **通过Python脚本**：
   ```python
   from src.models.models import UserStrategy
   UserStrategy.add_user_strategy(user_id, 'strategy_name')
   ```

## 使用示例

### 1. 用户注册时分配策略

用户在注册页面的"可查看的策略"文本框中输入：
```
strategy_a
strategy_b
example_strategy
```

### 2. API调用示例

**查看总持仓（带策略权限检查）**：
```bash
curl "http://localhost:5000/api/v1/positions/total?username=testuser&password=123456&strategies=strategy_a,strategy_b"
```

**获取用户策略统计**：
```bash
curl "http://localhost:5000/api/v1/user/strategies" \
  -H "Cookie: session=xxx"
```

**管理员为用户添加策略权限**：
```bash
curl -X POST "http://localhost:5000/api/v1/admin/user/2/strategies" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=xxx" \
  -d '{"strategy_name": "new_strategy"}'
```

## 注意事项

1. **向后兼容性**：现有用户默认没有任何策略权限，需要手动分配
2. **性能考虑**：策略权限检查会增加数据库查询，但通过索引优化性能
3. **日志监控**：定时任务会生成日志文件，建议定期清理
4. **权限管理**：只有超级管理员可以管理用户策略权限
5. **数据一致性**：删除用户时会自动删除相关的策略权限记录

## 故障排除

### 1. 数据库连接问题
确保 `src/config.py` 中的数据库配置正确

### 2. 权限问题
确保用户有相应策略的查看权限

### 3. 定时任务问题
检查定时任务的执行日志，确保Python环境和路径配置正确

### 4. API接口问题
检查用户登录状态和权限级别
