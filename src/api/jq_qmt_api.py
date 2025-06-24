import json
import base64
import time
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import requests
try:
    import jq_config
except:
    import src.api.jq_config as jq_config

class JQQMTAPI:
    def __init__(self, api_url=jq_config.API_URL, private_key_file=jq_config.PRIVATE_KEY_FILE, client_id="default_client", use_crypto_auth=jq_config.USE_CRYPTO_AUTH, simple_api_key=None):
        """初始化API客户端
        
        Args:
            private_key_pem: 私钥PEM字符串（用于加密认证，优先级高）
            private_key_file: 私钥文件路径（用于加密认证）
            client_id: 客户端ID
            use_crypto_auth: 是否使用加密认证
            simple_api_key: 简单API密钥（当不使用加密认证时）
        """
        self.api_url = api_url
        self.client_id = client_id
        self.use_crypto_auth = use_crypto_auth
        self.simple_api_key = simple_api_key
        
        if use_crypto_auth:
            private_key_path = private_key_file
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
    
    def _create_auth_header(self):
        """创建认证头"""
        if not self.use_crypto_auth:
            # 简单API密钥认证
            return {'X-API-Key': 'your-simple-api-key-here'}
        
        if not self.private_key:
            raise Exception("使用加密认证时必须提供私钥")
        
        # 创建认证数据
        auth_data = {
            'client_id': self.client_id,
            'timestamp': int(time.time())
        }
        
        # 创建签名
        message = json.dumps(auth_data, sort_keys=True)
        signature = self.private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # 编码认证信息
        auth_info = {
            'auth_data': auth_data,
            'signature': base64.b64encode(signature).decode('utf-8')
        }
        
        auth_token = base64.b64encode(
            json.dumps(auth_info).encode('utf-8')
        ).decode('utf-8')
        
        return {'X-Auth-Token': auth_token}
    
    def update_positions(self, strategy_name: str, positions: list):
        """
        更新策略持仓到数据库
        
        Args:
            strategy_name: 策略名称
            positions: 持仓列表，格式如：
                [
                    {
                        'code': '000001.XSHE',
                        'volume': 100,
                        'cost': 10.5
                    }
                ]
        """
        url = f'{self.api_url}/api/v1/positions/update'
        data = {
            'strategy_name': strategy_name,
            'positions': positions
        }
        
        # 添加认证头
        headers = self._create_auth_header()
        headers['Content-Type'] = 'application/json'
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f'更新持仓失败: {response.text}')
        
        return response.json()