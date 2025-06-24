from sqlalchemy.engine import URL

# 数据库配置
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': '127.0.0.1',     
    'username': 'username',  # 修改成你的数据库用户名
    'password': 'password',  # 修改成你的数据库密码
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
    
    # 密钥文件路径（相对于项目根目录）
    'PRIVATE_KEY_FILE': 'quant_id_rsa_pkcs8.pem',  # PKCS#8格式私钥文件
    'PUBLIC_KEY_FILE': 'quant_id_rsa_public.pem',   # X.509格式公钥文件
    
    'TOKEN_MAX_AGE': 300,  # 令牌有效期（秒）
    
    # 当加密禁用时的简单API密钥（可选）
    'SIMPLE_API_KEY': 'your-simple-api-key-here'
}