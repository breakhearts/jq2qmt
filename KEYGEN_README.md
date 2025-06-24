# 密钥生成工具使用说明

本项目提供了两个密钥生成脚本，用于快速生成JQ-QMT系统所需的RSA密钥对。

## 脚本文件

- `generate_keys.sh` - Linux/macOS 版本
- `generate_keys.bat` - Windows 版本

## 前置要求

### Linux/macOS
- 已安装 OpenSSL（通常系统自带）
- Bash shell 环境

### Windows
- 已安装 OpenSSL for Windows
  - 下载地址：https://slproweb.com/products/Win32OpenSSL.html
  - 或使用 Git for Windows 自带的 OpenSSL

## 使用方法

### Linux/macOS

```bash
# 进入项目目录
cd /path/to/jq2qmt

# 运行密钥生成脚本
./generate_keys.sh
```

### Windows

```cmd
REM 进入项目目录
cd C:\path\to\jq2qmt

REM 运行密钥生成脚本
generate_keys.bat
```

或者直接双击 `generate_keys.bat` 文件运行。

## 生成的文件

脚本会在当前目录生成以下三个文件：

1. **quant_id_rsa_new.pem** - 原始RSA私钥（4096位）
2. **quant_id_rsa_pkcs8.pem** - PKCS#8格式私钥（用于配置文件）
3. **quant_id_rsa_public.pem** - X.509格式公钥（用于配置文件）

## 配置步骤

1. **复制私钥到配置文件**
   ```bash
   # 查看PKCS#8私钥内容
   cat quant_id_rsa_pkcs8.pem
   ```
   将输出内容复制到 `src/config.py` 的 `CRYPTO_AUTH_CONFIG['PRIVATE_KEY']` 字段

2. **复制公钥到配置文件**
   ```bash
   # 查看公钥内容
   cat quant_id_rsa_public.pem
   ```
   将输出内容复制到 `src/config.py` 的 `CRYPTO_AUTH_CONFIG['PUBLIC_KEY']` 字段

## 安全注意事项

### 文件权限
- 私钥文件会自动设置为 600 权限（仅所有者可读写）
- 公钥文件设置为 644 权限（所有者可读写，其他人只读）

### 密钥管理
- **私钥文件包含敏感信息，切勿泄露给他人**
- 建议将密钥文件备份到安全位置
- 生产环境中建议使用环境变量存储密钥，而非直接写在代码中
- 定期轮换密钥以提高安全性

### 版本控制
- **不要将私钥文件提交到Git仓库**
- 项目的 `.gitignore` 文件已包含密钥文件的排除规则

## 故障排除

### OpenSSL 未找到
- **Linux**: `sudo apt-get install openssl` 或 `sudo yum install openssl`
- **macOS**: `brew install openssl`（如果系统自带版本有问题）
- **Windows**: 从官网下载安装 OpenSSL for Windows

### 权限错误
- **Linux/macOS**: 确保脚本有执行权限 `chmod +x generate_keys.sh`
- **Windows**: 以管理员身份运行命令提示符

### 文件已存在
- 脚本会检测现有密钥文件并询问是否覆盖
- 选择 'y' 覆盖，或 'N' 取消操作

## 自动化集成

可以将密钥生成集成到部署脚本中：

```bash
#!/bin/bash
# 部署脚本示例

# 生成密钥（如果不存在）
if [[ ! -f "quant_id_rsa_pkcs8.pem" ]]; then
    echo "生成新的密钥对..."
    ./generate_keys.sh
fi

# 继续其他部署步骤...
```

## 相关文档

- [API使用文档](API_USAGE.md)
- [项目README](README.md)
- [示例代码](example_usage.py)