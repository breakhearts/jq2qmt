# 内部API接口说明

## 概述

为了解决保存持仓时"缺少令牌"的问题，新增了一套内部API接口，使用密码验证而不是RSA验证，方便Web页面调用。

## 问题背景

原有的 `/api/v1/positions/update` 接口启用了RSA验证，在某些场景下可能出现"缺少令牌"的错误。为了提供更简单可靠的保存方式，新增了内部API接口。

## 新增功能

### 1. 内部持仓更新接口

**接口地址**: `POST /api/v1/positions/update/internal`

**认证方式**: 密码验证（而非RSA验证）

**密码传递方式**:
- 方式1: 请求头 `X-Internal-Password`
- 方式2: 请求体中的 `internal_password` 字段

**请求示例**:

```bash
# 方式1: 使用请求头
curl -X POST http://localhost:5366/api/v1/positions/update/internal \
  -H "Content-Type: application/json" \
  -H "X-Internal-Password: admin123" \
  -d '{
    "strategy_name": "TEST_STRATEGY",
    "positions": [
      {
        "code": "000001.SZ",
        "name": "平安银行",
        "volume": 1000,
        "cost": 12.50
      }
    ]
  }'

# 方式2: 使用请求体
curl -X POST http://localhost:5366/api/v1/positions/update/internal \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "TEST_STRATEGY",
    "positions": [
      {
        "code": "000001.SZ",
        "name": "平安银行",
        "volume": 1000,
        "cost": 12.50
      }
    ],
    "internal_password": "admin123"
  }'
```

### 2. 密码管理接口

#### 获取密码信息

**接口地址**: `GET /api/v1/internal/password/info`

**说明**: 获取当前密码状态信息（不包含密码本身）

**响应示例**:
```json
{
  "has_password": false,
  "default_password": "admin123",
  "message": "使用默认密码，建议通过数据库修改"
}
```

#### 设置新密码

**接口地址**: `POST /api/v1/internal/password/set`

**认证**: 需要提供当前密码

**请求示例**:
```bash
curl -X POST http://localhost:5366/api/v1/internal/password/set \
  -H "Content-Type: application/json" \
  -d '{
    "internal_password": "admin123",
    "new_password": "newpassword123"
  }'
```

## 密码管理

### 默认密码

系统默认密码为: `admin123`

### 修改密码的方法

#### 方法1: 通过API接口修改

使用 `/api/v1/internal/password/set` 接口，需要提供当前密码。

#### 方法2: 直接操作数据库

```sql
-- 查看当前密码信息
SELECT * FROM internal_passwords;

-- 设置新密码（SHA256哈希）
-- 例如设置密码为 "mynewpassword"
INSERT INTO internal_passwords (password_hash, created_time, updated_time) 
VALUES (
  SHA2('mynewpassword', 256), 
  NOW(), 
  NOW()
) 
ON DUPLICATE KEY UPDATE 
  password_hash = SHA2('mynewpassword', 256),
  updated_time = NOW();

-- 或者更新现有记录
UPDATE internal_passwords 
SET password_hash = SHA2('mynewpassword', 256), 
    updated_time = NOW() 
WHERE id = 1;
```

### 密码安全

- 密码使用SHA256哈希存储，不会明文保存
- 建议定期更换密码
- 密码长度至少6位
- 生产环境中务必修改默认密码

## 数据库表结构

新增了 `internal_passwords` 表：

```sql
CREATE TABLE internal_passwords (
  id INT PRIMARY KEY AUTO_INCREMENT,
  password_hash VARCHAR(64) NOT NULL,
  created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 使用示例

参考 `example_internal_api.py` 文件，包含了完整的使用示例：

```bash
python example_internal_api.py
```

## 错误处理

### 常见错误码

- `401`: 密码验证失败或缺少密码
- `400`: 请求数据格式错误
- `500`: 服务器内部错误

### 错误响应示例

```json
{
  "error": "密码验证失败",
  "message": "内部密码不正确"
}
```

## 与原有接口的区别

| 特性 | 原有接口 | 内部接口 |
|------|----------|----------|
| 接口地址 | `/api/v1/positions/update` | `/api/v1/positions/update/internal` |
| 认证方式 | RSA签名验证 | 密码验证 |
| 复杂度 | 高（需要生成签名） | 低（只需密码） |
| 适用场景 | 外部系统调用 | 内部Web页面调用 |
| 安全性 | 高 | 中等 |

## 注意事项

1. 内部接口仅用于内部系统调用，不建议暴露给外部
2. 定期更换密码以确保安全
3. 生产环境中务必修改默认密码
4. 可以通过防火墙等手段限制内部接口的访问
5. 建议在内网环境中使用，避免密码在公网传输

## 部署建议

1. 启动服务后，立即修改默认密码
2. 配置适当的访问控制策略
3. 定期备份数据库
4. 监控API调用日志