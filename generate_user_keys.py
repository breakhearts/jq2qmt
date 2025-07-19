#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为现有用户批量生成密钥对的辅助脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_rsa_keys():
    """生成RSA密钥对"""
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

def update_user_keys():
    """为所有没有密钥的用户生成密钥对"""
    try:
        # 初始化Flask应用和数据库
        from src.app import create_app
        from src.models.models import db, User
        
        app = create_app()
        
        with app.app_context():
            # 查找没有密钥的用户
            users_without_keys = User.query.filter(
                (User.private_key == None) | (User.public_key == None) |
                (User.private_key == '') | (User.public_key == '')
            ).all()
            
            if not users_without_keys:
                print("所有用户都已配置了密钥对")
                return
            
            print(f"找到 {len(users_without_keys)} 个需要生成密钥的用户：")
            
            for user in users_without_keys:
                print(f"为用户 {user.username} 生成密钥对...")
                
                # 生成密钥对
                private_pem, public_pem = generate_rsa_keys()
                
                # 更新用户密钥
                user.private_key = private_pem
                user.public_key = public_pem
                
                print(f"✓ 用户 {user.username} 的密钥对已生成")
            
            # 提交更改
            db.session.commit()
            print(f"\n成功为 {len(users_without_keys)} 个用户生成了密钥对")
            
    except Exception as e:
        print(f"生成密钥时出错: {e}")
        import traceback
        traceback.print_exc()

def list_users_with_keys():
    """列出所有用户的密钥状态"""
    try:
        from src.app import create_app
        from src.models.models import db, User
        
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            print("用户密钥配置状态：")
            print("-" * 60)
            print(f"{'用户名':<20} {'私钥':<10} {'公钥':<10} {'状态':<15}")
            print("-" * 60)
            
            for user in users:
                has_private = "✓" if user.private_key else "✗"
                has_public = "✓" if user.public_key else "✗"
                status = "完整" if (user.private_key and user.public_key) else "不完整"
                
                print(f"{user.username:<20} {has_private:<10} {has_public:<10} {status:<15}")
                
    except Exception as e:
        print(f"查询用户信息时出错: {e}")

if __name__ == "__main__":
    print("基于数据库的认证系统 - 密钥管理工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "generate":
            print("开始为所有用户生成密钥对...")
            update_user_keys()
        elif command == "list":
            print("查询用户密钥配置状态...")
            list_users_with_keys()
        else:
            print("无效的命令。可用命令：generate, list")
    else:
        print("使用方法：")
        print("  python generate_user_keys.py generate  # 为所有用户生成密钥")
        print("  python generate_user_keys.py list      # 查看用户密钥状态")
