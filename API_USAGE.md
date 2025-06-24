# JQ-QMT API 使用指南

## 概述

JQ-QMT API 支持两种认证方式：
1. **加密认证**：使用RSA密钥对进行签名验证（推荐用于生产环境）
2. **简单API密钥认证**：使用预共享密钥（适用于开发和测试）

## 认证配置

### 1. 加密认证配置

在 `src/config.py` 中：

```python
CRYPTO_AUTH_CONFIG = {
    'ENABLED': True,  # 启用加密认证
    'PRIVATE_KEY': '...',  # 服务端私钥（PKCS#8格式）
    'PUBLIC_KEY': '...',   # 客户端公钥（X.509格式）
    'TOKEN_MAX_AGE': 300,  # 令牌有效期（秒）
}
```

### 2. 简单API密钥配置

```python
CRYPTO_AUTH_CONFIG = {
    'ENABLED': False,  # 禁用加密认证
    'SIMPLE_API_KEY': 'your-api-key-here'  # API密钥
}
```

## 客户端使用

### 1. 使用加密认证

```python
from api.jq_qmt_api import JQQMTAPI
from config import CRYPTO_AUTH_CONFIG

# 从配置获取私钥
private_key_pem = CRYPTO_AUTH_CONFIG['PRIVATE_KEY']

# 创建API客户端

# 方式1：使用PEM字符串（适用于配置文件中的密钥）
api = JQQMTAPI(
    private_key_pem=private_key_pem,
    client_id="client1",
    use_crypto_auth=True
)

# 方式2：使用文件路径（推荐方式，更安全）
api = JQQMTAPI(
    private_key_file="quant_id_rsa_pkcs8.pem",  # 相对于项目根目录
    client_id="client1",
    use_crypto_auth=True
)

# 方式3：使用绝对路径
api = JQQMTAPI(
    private_key_file="/path/to/your/quant_id_rsa_pkcs8.pem",
    client_id="client1",
    use_crypto_auth=True
)

# 更新持仓
positions = [
    {
        'code': '000001.XSHE',
        'volume': 100,
        'cost': 10.5
    }
]

result = api.update_positions("my_strategy", positions)
print(result)
```

### 2. 使用简单API密钥认证

```python
from api.jq_qmt_api import JQQMTAPI

# 创建API客户端（简单认证）
api = JQQMTAPI(use_crypto_auth=False)

# 更新持仓
positions = [
    {
        'code': '000001.XSHE',
        'volume': 100,
        'cost': 10.5
    }
]

result = api.update_positions("my_strategy", positions)
print(result)
```

### 3. 从文件加载私钥

```python
# 从文件读取私钥
with open('quant_id_rsa_pkcs8.pem', 'r') as f:
    private_key_pem = f.read()

api = JQQMTAPI(
    private_key_pem=private_key_pem,
    client_id="client1",
    use_crypto_auth=True
)
```

## API 端点

### 1. 更新持仓

**POST** `/api/v1/positions/update`

**请求体：**
```json
{
    "strategy_name": "my_strategy",
    "positions": [
        {
            "code": "000001.XSHE",
            "volume": 100,
            "cost": 10.5
        }
    ]
}
```

**认证头（加密认证）：**
```
X-Auth-Token: <base64编码的认证令牌>
```

**认证头（简单认证）：**
```
X-API-Key: your-api-key-here
```

### 2. 获取认证信息

**GET** `/api/v1/auth/info`

返回当前认证系统的配置信息。

### 3. 查询持仓

- **GET** `/api/v1/positions/strategy/<strategy_name>` - 获取指定策略持仓
- **GET** `/api/v1/positions/total?strategies=strategy1,strategy2` - 获取合并持仓
- **GET** `/api/v1/positions/all` - 获取所有策略持仓

## 认证流程详解

### 加密认证流程

1. **客户端**创建认证数据：
   ```json
   {
       "client_id": "client1",
       "timestamp": 1640995200
   }
   ```

2. **客户端**使用私钥对认证数据进行签名

3. **客户端**将认证数据和签名编码为Base64，放入请求头

4. **服务端**验证：
   - 检查客户端ID是否在允许列表中
   - 检查时间戳是否在有效期内
   - 使用公钥验证签名

### 简单认证流程

1. **客户端**在请求头中包含API密钥：`X-API-Key: your-api-key`
2. **服务端**验证API密钥是否匹配配置中的值

## 安全建议

### 密钥管理
1. **推荐使用文件方式**：优先使用 `private_key_file` 参数从文件读取密钥，而不是在代码中硬编码
2. **私钥保护**：确保私钥文件权限正确（`chmod 600 quant_id_rsa_pkcs8.pem`）
3. **密钥存储位置**：
   - 开发环境：可放在项目根目录
   - 生产环境：建议放在安全目录（如 `/etc/ssl/private/`）
4. **版本控制**：密钥文件不应提交到版本控制系统（添加到 `.gitignore`）
5. **密钥轮换**：定期更换密钥对

### 网络安全
6. **生产环境**建议使用加密认证
7. **HTTPS**：生产环境必须使用HTTPS
8. **环境变量**：敏感配置信息存储在环境变量中

### 文件路径配置
- **相对路径**：相对于项目根目录（推荐用于开发环境）
- **绝对路径**：用于生产环境的固定位置

## 错误处理

常见错误码：
- `401` - 认证失败
- `400` - 请求数据格式错误
- `500` - 服务器内部错误

## 示例代码

完整的使用示例请参考 `example_usage.py` 文件。

## 故障排除

1. **密钥格式错误**：确保使用PKCS#8格式的私钥和X.509格式的公钥
2. **时间同步**：确保客户端和服务端时间同步
3. **网络连接**：检查API_URL配置是否正确