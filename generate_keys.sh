#!/bin/bash

# JQ-QMT 密钥对生成脚本
# 用于生成RSA密钥对，包括PKCS#8格式私钥和X.509格式公钥

set -e  # 遇到错误时退出

echo "=== JQ-QMT 密钥对生成工具 ==="
echo

# 检查OpenSSL是否可用
if ! command -v openssl &> /dev/null; then
    echo "错误: 未找到 openssl 命令，请先安装 OpenSSL"
    exit 1
fi

# 设置密钥文件名
PRIVATE_KEY_FILE="quant_id_rsa_new.pem"
PKCS8_KEY_FILE="quant_id_rsa_pkcs8.pem"
PUBLIC_KEY_FILE="quant_id_rsa_public.pem"

# 检查是否已存在密钥文件
if [[ -f "$PRIVATE_KEY_FILE" || -f "$PKCS8_KEY_FILE" || -f "$PUBLIC_KEY_FILE" ]]; then
    echo "警告: 发现已存在的密钥文件:"
    [[ -f "$PRIVATE_KEY_FILE" ]] && echo "  - $PRIVATE_KEY_FILE"
    [[ -f "$PKCS8_KEY_FILE" ]] && echo "  - $PKCS8_KEY_FILE"
    [[ -f "$PUBLIC_KEY_FILE" ]] && echo "  - $PUBLIC_KEY_FILE"
    echo
    read -p "是否覆盖现有文件? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi
fi

echo "开始生成密钥对..."
echo

# 步骤1: 生成4096位RSA私钥
echo "1. 生成RSA私钥 ($PRIVATE_KEY_FILE)..."
openssl genrsa -out "$PRIVATE_KEY_FILE" 4096
if [[ $? -eq 0 ]]; then
    echo "   ✓ RSA私钥生成成功"
else
    echo "   ✗ RSA私钥生成失败"
    exit 1
fi
echo

# 步骤2: 转换为PKCS#8格式
echo "2. 转换为PKCS#8格式 ($PKCS8_KEY_FILE)..."
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in "$PRIVATE_KEY_FILE" -out "$PKCS8_KEY_FILE"
if [[ $? -eq 0 ]]; then
    echo "   ✓ PKCS#8格式私钥生成成功"
else
    echo "   ✗ PKCS#8格式转换失败"
    exit 1
fi
echo

# 步骤3: 提取公钥
echo "3. 提取公钥 ($PUBLIC_KEY_FILE)..."
openssl rsa -in "$PRIVATE_KEY_FILE" -pubout -out "$PUBLIC_KEY_FILE"
if [[ $? -eq 0 ]]; then
    echo "   ✓ 公钥提取成功"
else
    echo "   ✗ 公钥提取失败"
    exit 1
fi
echo

echo "=== 密钥生成完成 ==="
echo
echo "生成的文件:"
echo "  - $PRIVATE_KEY_FILE      (原始RSA私钥)"
echo "  - $PKCS8_KEY_FILE   (PKCS#8格式私钥，用于配置)"
echo "  - $PUBLIC_KEY_FILE    (X.509格式公钥，用于配置)"
echo
echo "下一步:"
echo "1. 将 $PKCS8_KEY_FILE 的内容复制到 src/config.py 的 PRIVATE_KEY 字段"
echo "2. 将 $PUBLIC_KEY_FILE 的内容复制到 src/config.py 的 PUBLIC_KEY 字段"
echo "3. 妥善保管私钥文件，不要泄露给他人"
echo
echo "安全提醒:"
echo "- 私钥文件包含敏感信息，请设置适当的文件权限"
echo "- 建议备份密钥文件到安全位置"
echo "- 生产环境中建议使用环境变量而非直接在代码中存储密钥"

# 设置文件权限
chmod 600 "$PRIVATE_KEY_FILE" "$PKCS8_KEY_FILE"
chmod 644 "$PUBLIC_KEY_FILE"

echo
echo "文件权限已设置完成"