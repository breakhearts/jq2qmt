#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JQ-QMT API 使用示例
演示如何使用加密认证和简单API密钥两种方式调用API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api.jq_qmt_api import JQQMTAPI
from config import CRYPTO_AUTH_CONFIG

def example_crypto_auth():
    """使用加密认证的示例"""
    print("=== 使用加密认证 ===")
    
    # 从配置文件获取私钥
    private_key_pem = CRYPTO_AUTH_CONFIG['PRIVATE_KEY']
    
    # 示例1：使用PEM字符串加载密钥
    api = JQQMTAPI(
        private_key_pem=private_key_pem,
        client_id="client1",  # 客户端ID
        use_crypto_auth=True
    )
    
    # 示例2：使用文件路径加载密钥（推荐方式）
    # api = JQQMTAPI(
    #     private_key_file="quant_id_rsa_pkcs8.pem",  # 相对于项目根目录的路径
    #     client_id="client1",
    #     use_crypto_auth=True
    # )
    
    # 示例3：使用绝对路径加载密钥
    # api = JQQMTAPI(
    #     private_key_file="/path/to/your/quant_id_rsa_pkcs8.pem",  # 绝对路径
    #     client_id="client1",
    #     use_crypto_auth=True
    # )
    
    # 示例持仓数据
    positions = [
        {
            'code': '000001.XSHE',
            'volume': 100,
            'cost': 10.5
        },
        {
            'code': '000002.XSHE', 
            'volume': 200,
            'cost': 15.8
        }
    ]
    
    try:
        # 更新持仓
        result = api.update_positions("my_strategy", positions)
        print(f"更新成功: {result}")
    except Exception as e:
        print(f"更新失败: {e}")

def example_simple_auth():
    """使用简单API密钥认证的示例"""
    print("\n=== 使用简单API密钥认证 ===")
    
    # 创建API客户端（使用简单认证）
    api = JQQMTAPI(
        use_crypto_auth=False
    )
    
    # 示例持仓数据
    positions = [
        {
            'code': '000001.XSHE',
            'volume': 150,
            'cost': 12.3
        }
    ]
    
    try:
        # 更新持仓
        result = api.update_positions("simple_strategy", positions)
        print(f"更新成功: {result}")
    except Exception as e:
        print(f"更新失败: {e}")

def example_load_key_from_file():
    """从文件加载私钥的示例"""
    print("\n=== 从文件加载私钥 ===")
    
    try:
        # 从文件读取私钥
        with open('quant_id_rsa_pkcs8.pem', 'r') as f:
            private_key_pem = f.read()
        
        # 创建API客户端
        api = JQQMTAPI(
            private_key_pem=private_key_pem,
            client_id="client2",
            use_crypto_auth=True
        )
        
        positions = [
            {
                'code': '000003.XSHE',
                'volume': 300,
                'cost': 8.9
            }
        ]
        
        result = api.update_positions("file_key_strategy", positions)
        print(f"使用文件密钥更新成功: {result}")
        
    except FileNotFoundError:
        print("密钥文件未找到，请确保 quant_id_rsa_pkcs8.pem 文件存在")
    except Exception as e:
        print(f"使用文件密钥更新失败: {e}")

if __name__ == "__main__":
    print("JQ-QMT API 使用示例")
    print("注意：运行前请确保：")
    print("1. 服务器正在运行")
    print("2. API_URL 配置正确")
    print("3. 认证配置正确")
    print("\n" + "="*50)
    
    # 运行示例
    example_crypto_auth()
    example_simple_auth()
    example_load_key_from_file()
    
    print("\n" + "="*50)
    print("示例完成")