#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于数据库的认证系统使用示例
展示如何为用户设置密钥对并使用新的认证系统
"""

import json
import base64
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# 示例：生成用户密钥对并保存到数据库
def generate_user_keys():
    """生成用户的RSA密钥对"""
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # 获取公钥
    public_key = private_key.public_key()
    
    # 序列化私钥（PKCS#8格式）
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # 序列化公钥（X.509格式）
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem

def create_auth_token(private_key_pem, client_id):
    """创建认证令牌"""
    # 加载私钥
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None
    )
    
    # 创建认证数据
    auth_data = {
        'client_id': client_id,
        'timestamp': int(time.time()),
        'action': 'api_access'
    }
    
    # 创建签名
    message = json.dumps(auth_data, sort_keys=True)
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # 编码签名
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # 创建认证令牌
    auth_info = {
        'auth_data': auth_data,
        'signature': signature_b64
    }
    
    # 编码认证令牌
    auth_token = base64.b64encode(
        json.dumps(auth_info).encode('utf-8')
    ).decode('utf-8')
    
    return auth_token

# 示例用法
if __name__ == "__main__":
    # 1. 生成密钥对
    private_pem, public_pem = generate_user_keys()
    print("生成的私钥：")
    print(private_pem)
    print("\n生成的公钥：")
    print(public_pem)
    
    # 2. 创建认证令牌
    client_id = "test_user"
    auth_token = create_auth_token(private_pem, client_id)
    print(f"\n为用户 {client_id} 生成的认证令牌：")
    print(auth_token)
    
    print(f"""
使用说明：
1. 将生成的密钥对保存到数据库的 users 表中对应用户的 private_key 和 public_key 字段
2. 客户端使用私钥生成认证令牌
3. 在API请求中添加请求头：X-Auth-Token: {auth_token}
4. 服务端会自动从数据库读取该用户的公钥进行验证

数据库更新示例（需要先确保用户存在）：
UPDATE users SET 
    private_key = '{private_pem.replace(chr(10), chr(92) + 'n')}',
    public_key = '{public_pem.replace(chr(10), chr(92) + 'n')}'
WHERE username = '{client_id}';
""")
