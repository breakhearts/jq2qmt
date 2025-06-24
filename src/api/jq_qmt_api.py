import json
import base64
import time
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import requests
from kuanke.user_space_api import *
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
            self.private_key = serialization.load_pem_private_key(
                read_file(private_key_file),
                password=None,
                backend=default_backend()
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
    
    def get_stock_name(self, code: str) -> str:
        """
        使用聚宽API获取股票名称
        
        Args:
            code: 股票代码，如 '000001.XSHE'
            
        Returns:
            股票名称，如果获取失败则返回股票代码
        """
        try:
            security_info = get_security_info(code)
            return security_info.display_name
        except Exception as e:
            print(f"获取股票名称失败 {code}: {e}")
            return code
    
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
        # 为每个持仓添加股票名称
        enriched_positions = []
        for pos in positions:
            enriched_pos = pos.copy()
            enriched_pos['name'] = self.get_stock_name(pos['code'])
            enriched_positions.append(enriched_pos)
        
        url = f'{self.api_url}/api/v1/positions/update'
        data = {
            'strategy_name': strategy_name,
            'positions': enriched_positions
        }
        
        # 添加认证头
        headers = self._create_auth_header()
        headers['Content-Type'] = 'application/json'
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f'更新持仓失败: {response.text}')
        
        return response.json()