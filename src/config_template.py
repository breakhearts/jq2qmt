from sqlalchemy.engine import URL

# 数据库配置
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': '127.0.0.1',
    'username': 'username',
    'password': 'password',
    'database': 'quant',
    'port': 3306
}

# SQLAlchemy配置
SQLALCHEMY_DATABASE_URI = URL.create(**DB_CONFIG)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# API配置
API_HOST = '0.0.0.0'
API_PORT = 5366
API_PREFIX = '/api/v1'

# 加密认证配置
CRYPTO_AUTH_CONFIG = {
    # 是否启用加密认证（True: 启用, False: 禁用）
    'ENABLED': True,
    
    # 服务端私钥（用于验证客户端签名）
    'PRIVATE_KEY': '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
wxFrKzahT7DcoTqPiHXQYiwfEnLasoCdTKz8kHp6zYKWpEAg+Q==
-----END PRIVATE KEY-----''',
    
    # 客户端公钥（用于验证客户端身份）
    'PUBLIC_KEY': '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCgcMRays2
oU+w3KE6j4h10GIsHxJy2rKAnUys/JB6es2ClqRAIPk=
-----END PUBLIC KEY-----''',
    
    'TOKEN_MAX_AGE': 300,  # 令牌有效期（秒）
    'ALLOWED_CLIENTS': ['client1', 'client2'],  # 允许的客户端ID
    
    # 当加密禁用时的简单API密钥（可选）
    'SIMPLE_API_KEY': 'your-simple-api-key-here'
}