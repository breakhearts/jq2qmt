#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内部API使用示例
演示如何使用密码验证的内部持仓更新接口
"""

import requests
import json

# API配置
API_BASE_URL = "http://localhost:5366"
INTERNAL_PASSWORD = "admin123"  # 默认密码，建议修改

def test_internal_password_info():
    """测试获取内部密码信息"""
    print("\n=== 获取内部密码信息 ===")
    url = f"{API_BASE_URL}/api/v1/internal/password/info"
    
    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_update_positions_internal():
    """测试内部持仓更新接口"""
    print("\n=== 测试内部持仓更新接口 ===")
    url = f"{API_BASE_URL}/api/v1/positions/update/internal"
    
    # 测试数据
    data = {
        "strategy_name": "TEST_STRATEGY_INTERNAL",
        "positions": [
            {
                "code": "000001.SZ",
                "name": "平安银行",
                "volume": 1000,
                "cost": 12.50
            },
            {
                "code": "000002.SZ",
                "name": "万科A",
                "volume": 500,
                "cost": 25.80
            }
        ],
        "internal_password": INTERNAL_PASSWORD  # 在请求体中提供密码
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_update_positions_internal_with_header():
    """测试使用请求头传递密码的内部持仓更新接口"""
    print("\n=== 测试内部持仓更新接口（请求头密码） ===")
    url = f"{API_BASE_URL}/api/v1/positions/update/internal"
    
    # 测试数据
    data = {
        "strategy_name": "TEST_STRATEGY_HEADER",
        "positions": [
            {
                "code": "600000.SH",
                "name": "浦发银行",
                "volume": 800,
                "cost": 8.90
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Password": INTERNAL_PASSWORD  # 在请求头中提供密码
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_set_new_password():
    """测试设置新密码"""
    print("\n=== 测试设置新密码 ===")
    url = f"{API_BASE_URL}/api/v1/internal/password/set"
    
    data = {
        "internal_password": INTERNAL_PASSWORD,  # 当前密码
        "new_password": "newpassword123"  # 新密码
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_wrong_password():
    """测试错误密码"""
    print("\n=== 测试错误密码 ===")
    url = f"{API_BASE_URL}/api/v1/positions/update/internal"
    
    data = {
        "strategy_name": "TEST_WRONG_PASSWORD",
        "positions": [],
        "internal_password": "wrongpassword"  # 错误密码
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_missing_password():
    """测试缺少密码"""
    print("\n=== 测试缺少密码 ===")
    url = f"{API_BASE_URL}/api/v1/positions/update/internal"
    
    data = {
        "strategy_name": "TEST_NO_PASSWORD",
        "positions": []
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("内部API测试开始...")
    print(f"API地址: {API_BASE_URL}")
    print(f"使用密码: {INTERNAL_PASSWORD}")
    
    try:
        # 测试获取密码信息
        test_internal_password_info()
        
        # 测试正常的内部持仓更新
        test_update_positions_internal()
        
        # 测试使用请求头传递密码
        test_update_positions_internal_with_header()
        
        # 测试错误场景
        test_wrong_password()
        test_missing_password()
        
        # 测试设置新密码（注释掉，避免意外修改密码）
        # test_set_new_password()
        
        print("\n=== 测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到API服务器")
        print("请确保服务器正在运行: python src/app.py")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")