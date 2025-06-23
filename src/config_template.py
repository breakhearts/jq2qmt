from sqlalchemy.engine.url import URL

# 数据库配置
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': '127.0.0.1',
    'username': 'username',         # 替换成你的数据库用户名
    'password': 'password',         # 替换成你的数据库密码
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