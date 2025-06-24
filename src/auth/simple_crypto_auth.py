import time
import json
import base64
import time
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from functools import wraps
from flask import request, jsonify

class SimpleCryptoAuth:
    def __init__(self, private_key_pem=None, public_key_pem=None, private_key_file=None, public_key_file=None):
        """初始化加密认证
        
        Args:
            private_key_pem: 私钥PEM字符串（优先级高）
            public_key_pem: 公钥PEM字符串（优先级高）
            private_key_file: 私钥文件路径
            public_key_file: 公钥文件路径
        """
        # 加载私钥
        if private_key_pem:
            # 从字符串加载私钥
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
        elif private_key_file:
            # 从文件加载私钥
            private_key_path = self._get_key_file_path(private_key_file)
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
        else:
            raise ValueError("必须提供私钥PEM字符串或私钥文件路径")
        
        # 加载公钥
        if public_key_pem:
            # 从字符串加载公钥
            self.public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
        elif public_key_file:
            # 从文件加载公钥
            public_key_path = self._get_key_file_path(public_key_file)
            with open(public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read()
                )
        else:
            raise ValueError("必须提供公钥PEM字符串或公钥文件路径")
    
    def _get_key_file_path(self, key_file):
        """获取密钥文件的绝对路径"""
        if os.path.isabs(key_file):
            return key_file
        else:
            # 相对路径，相对于项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(project_root, key_file)
    
    def verify_signature(self, message, signature_b64):
        """验证签名"""
        try:
            signature = base64.b64decode(signature_b64)
            self.public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, Exception):
            return False
    
    def verify_auth_token(self, auth_data, signature, max_age=300):
        """验证认证令牌"""
        try:
            # 检查时间戳
            current_time = int(time.time())
            if current_time - auth_data['timestamp'] > max_age:
                return False, "令牌已过期"
            
            # 验证签名
            message = json.dumps(auth_data, sort_keys=True)
            if not self.verify_signature(message, signature):
                return False, "签名验证失败"
            
            return True, "验证成功"
        except Exception as e:
            return False, f"验证错误: {str(e)}"

# 全局认证实例（在app.py中初始化）
crypto_auth = None

def require_auth(f):
    """统一认证装饰器（支持加密和简单API密钥两种模式）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import CRYPTO_AUTH_CONFIG
        
        # 检查是否启用加密认证
        if CRYPTO_AUTH_CONFIG.get('ENABLED', True):
            return _require_crypto_auth(f)(*args, **kwargs)
        else:
            return _require_simple_auth(f)(*args, **kwargs)
    
    return decorated_function

def _require_crypto_auth(f):
    """加密认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not crypto_auth:
            return jsonify({'error': '认证系统未初始化'}), 500
        
        try:
            # 从请求头获取认证信息
            auth_header = request.headers.get('X-Auth-Token')
            if not auth_header:
                return jsonify({'error': '缺少认证令牌'}), 401
            
            # 解析认证数据
            auth_info = json.loads(base64.b64decode(auth_header).decode('utf-8'))
            auth_data = auth_info.get('auth_data')
            signature = auth_info.get('signature')
            
            if not auth_data or not signature:
                return jsonify({'error': '认证令牌格式错误'}), 401
            
            # 从配置获取参数
            from config import CRYPTO_AUTH_CONFIG
            max_age = CRYPTO_AUTH_CONFIG.get('TOKEN_MAX_AGE', 300)
            
            # 验证令牌
            is_valid, message = crypto_auth.verify_auth_token(
                auth_data, signature, max_age
            )
            if not is_valid:
                return jsonify({'error': f'认证失败: {message}'}), 401
            
            # 将客户端ID添加到请求上下文
            request.client_id = auth_data.get('client_id')
            request.auth_type = 'crypto'
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': f'认证处理错误: {str(e)}'}), 401
    
    return decorated_function

def _require_simple_auth(f):
    """简单API密钥认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from config import CRYPTO_AUTH_CONFIG
            
            # 从请求头或查询参数获取API密钥
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                api_key = request.args.get('api_key')
            
            # 验证API密钥
            expected_key = CRYPTO_AUTH_CONFIG.get('SIMPLE_API_KEY')
            if not api_key or api_key != expected_key:
                return jsonify({'error': '无效的API密钥或缺少API密钥'}), 401
            
            # 设置请求上下文
            request.client_id = 'simple_auth_client'
            request.auth_type = 'simple'
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': f'认证处理错误: {str(e)}'}), 401
    
    return decorated_function

# 保持向后兼容
require_crypto_auth = require_auth