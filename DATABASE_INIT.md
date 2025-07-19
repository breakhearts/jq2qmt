# 数据库初始化说明

本文档说明如何初始化JQ-QMT项目的数据库。

## 快速开始

### 方法1: 自动初始化（推荐）

**Windows用户:**
```bash
# 双击运行批处理文件
init_database.bat

# 或在命令行运行
.\init_database.bat
```

**Python脚本:**
```bash
python setup_database.py
```

### 方法2: 手动SQL初始化

如果自动初始化失败，可以手动执行SQL文件：

1. 连接到MySQL服务器
2. 执行 `database_schema.sql` 文件
3. 验证表结构和数据

```sql
mysql -h your_host -u your_username -p < database_schema.sql
```

## 数据库结构

### 数据表

#### 1. strategy_positions（策略持仓表）
```sql
CREATE TABLE `strategy_positions` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `strategy_name` varchar(100) NOT NULL COMMENT '策略名称',
    `positions` json NOT NULL COMMENT '持仓数据JSON',
    `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_strategy_name` (`strategy_name`)
);
```

**字段说明:**
- `id`: 主键，自增
- `strategy_name`: 策略名称，唯一
- `positions`: 持仓数据，JSON格式
- `update_time`: 更新时间，自动维护

**JSON格式示例:**
```json
[
    {
        "code": "000001.SZ",
        "name": "平安银行", 
        "volume": 1000,
        "cost": 12.50
    },
    {
        "code": "600000.SH",
        "name": "浦发银行",
        "volume": 500, 
        "cost": 8.20
    }
]
```

#### 2. internal_passwords（内部密码表）
```sql
CREATE TABLE `internal_passwords` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `password_hash` varchar(64) NOT NULL COMMENT '密码哈希值',
    `created_time` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
);
```

**字段说明:**
- `id`: 主键，自增
- `password_hash`: SHA256密码哈希值
- `created_time`: 创建时间
- `updated_time`: 更新时间

## 默认数据

### 默认密码
- **用户名**: 无（仅密码验证）
- **密码**: `admin123`
- **用途**: 内部API接口认证

### 示例策略

#### example_strategy
```json
[
    {"code": "000001.SZ", "name": "平安银行", "volume": 1000, "cost": 12.5},
    {"code": "600000.SH", "name": "浦发银行", "volume": 500, "cost": 8.2}
]
```

#### hand_strategy
```json
[
    {"code": "000002.SZ", "name": "万科A", "volume": 2000, "cost": 15.8},
    {"code": "600036.SH", "name": "招商银行", "volume": 1500, "cost": 45.2}
]
```

## 配置说明

### 数据库配置 (src/config.py)
```python
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': 'your_mysql_host',
    'username': 'your_username', 
    'password': 'your_password',
    'database': 'quant_qmt',
    'port': 3306
}
```

**配置项说明:**
- `host`: MySQL服务器地址
- `username`: 数据库用户名
- `password`: 数据库密码
- `database`: 数据库名称
- `port`: MySQL端口（默认3306）

## 验证初始化

### 1. 检查表结构
```sql
USE quant_qmt;
SHOW TABLES;
```

应该看到:
```
+-------------------------+
| Tables_in_quant_qmt     |
+-------------------------+
| internal_passwords      |
| strategy_positions      |
+-------------------------+
```

### 2. 检查默认数据
```sql
-- 检查策略数量
SELECT COUNT(*) as strategy_count FROM strategy_positions;

-- 检查密码记录
SELECT COUNT(*) as password_count FROM internal_passwords;

-- 查看策略列表
SELECT strategy_name, JSON_LENGTH(positions) as position_count, update_time 
FROM strategy_positions;
```

### 3. API测试
启动应用后测试API接口：

```bash
# 获取所有策略
curl http://localhost:5366/api/v1/positions/all

# 获取总持仓
curl http://localhost:5366/api/v1/positions/total

# 测试密码验证
curl -X POST http://localhost:5366/api/v1/internal/password/info
```

## 故障排除

### 常见问题

#### 1. 连接失败
**错误**: `Can't connect to MySQL server`
**解决**:
- 检查MySQL服务是否运行
- 验证config.py中的连接参数
- 确认网络连接和防火墙设置

#### 2. 权限不足
**错误**: `Access denied for user`
**解决**:
- 检查数据库用户名和密码
- 确认用户有CREATE、INSERT权限
- 联系数据库管理员

#### 3. 数据库不存在
**错误**: `Unknown database 'quant_qmt'`
**解决**:
- 手动创建数据库: `CREATE DATABASE quant_qmt;`
- 或修改config.py中的database名称

#### 4. 表已存在
**错误**: `Table 'strategy_positions' already exists`
**解决**:
- 这是正常情况，表示数据库已初始化
- 可以跳过建表步骤

#### 5. JSON字段不支持
**错误**: `JSON column not supported`
**解决**:
- 升级MySQL到5.7+版本
- 或使用TEXT字段替代JSON

### 重置数据库

如果需要重新初始化数据库：

```sql
-- 删除所有表
DROP TABLE IF EXISTS strategy_positions;
DROP TABLE IF EXISTS internal_passwords;

-- 重新运行初始化脚本
-- 或执行 database_schema.sql
```

### 备份和恢复

**备份数据库:**
```bash
mysqldump -h host -u username -p quant_qmt > backup.sql
```

**恢复数据库:**
```bash
mysql -h host -u username -p quant_qmt < backup.sql
```

## 高级配置

### 性能优化

1. **索引优化**
```sql
-- 为常用查询添加索引
ALTER TABLE strategy_positions ADD INDEX idx_update_time (update_time);
```

2. **JSON查询优化**
```sql
-- 为JSON字段创建虚拟列和索引（MySQL 8.0+）
ALTER TABLE strategy_positions 
ADD COLUMN position_count INT GENERATED ALWAYS AS (JSON_LENGTH(positions)) STORED,
ADD INDEX idx_position_count (position_count);
```

### 监控设置

1. **慢查询日志**
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

2. **性能监控**
```sql
-- 查看表大小
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size(MB)'
FROM information_schema.TABLES 
WHERE table_schema = 'quant_qmt';
```

---

**更多信息请参考项目主README和API文档**
