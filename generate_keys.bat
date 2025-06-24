@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM JQ-QMT 密钥对生成脚本 (Windows版本)
REM 用于生成RSA密钥对，包括PKCS#8格式私钥和X.509格式公钥

echo === JQ-QMT 密钥对生成工具 ===
echo.

REM 检查OpenSSL是否可用
openssl version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 openssl 命令，请先安装 OpenSSL
    echo 下载地址: https://slproweb.com/products/Win32OpenSSL.html
    pause
    exit /b 1
)

REM 设置密钥文件名
set PRIVATE_KEY_FILE=quant_id_rsa_new.pem
set PKCS8_KEY_FILE=quant_id_rsa_pkcs8.pem
set PUBLIC_KEY_FILE=quant_id_rsa_public.pem

REM 检查是否已存在密钥文件
set FILES_EXIST=0
if exist "%PRIVATE_KEY_FILE%" set FILES_EXIST=1
if exist "%PKCS8_KEY_FILE%" set FILES_EXIST=1
if exist "%PUBLIC_KEY_FILE%" set FILES_EXIST=1

if %FILES_EXIST%==1 (
    echo 警告: 发现已存在的密钥文件:
    if exist "%PRIVATE_KEY_FILE%" echo   - %PRIVATE_KEY_FILE%
    if exist "%PKCS8_KEY_FILE%" echo   - %PKCS8_KEY_FILE%
    if exist "%PUBLIC_KEY_FILE%" echo   - %PUBLIC_KEY_FILE%
    echo.
    set /p "OVERWRITE=是否覆盖现有文件? (y/N): "
    if /i not "!OVERWRITE!"=="y" (
        echo 操作已取消
        pause
        exit /b 0
    )
)

echo 开始生成密钥对...
echo.

REM 步骤1: 生成4096位RSA私钥
echo 1. 生成RSA私钥 (%PRIVATE_KEY_FILE%)...
openssl genrsa -out "%PRIVATE_KEY_FILE%" 4096
if errorlevel 1 (
    echo    ✗ RSA私钥生成失败
    pause
    exit /b 1
)
echo    ✓ RSA私钥生成成功
echo.

REM 步骤2: 转换为PKCS#8格式
echo 2. 转换为PKCS#8格式 (%PKCS8_KEY_FILE%)...
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in "%PRIVATE_KEY_FILE%" -out "%PKCS8_KEY_FILE%"
if errorlevel 1 (
    echo    ✗ PKCS#8格式转换失败
    pause
    exit /b 1
)
echo    ✓ PKCS#8格式私钥生成成功
echo.

REM 步骤3: 提取公钥
echo 3. 提取公钥 (%PUBLIC_KEY_FILE%)...
openssl rsa -in "%PRIVATE_KEY_FILE%" -pubout -out "%PUBLIC_KEY_FILE%"
if errorlevel 1 (
    echo    ✗ 公钥提取失败
    pause
    exit /b 1
)
echo    ✓ 公钥提取成功
echo.

echo === 密钥生成完成 ===
echo.
echo 生成的文件:
echo   - %PRIVATE_KEY_FILE%      (原始RSA私钥)
echo   - %PKCS8_KEY_FILE%   (PKCS#8格式私钥，用于配置)
echo   - %PUBLIC_KEY_FILE%    (X.509格式公钥，用于配置)
echo.
echo 下一步:
echo 1. 将 %PKCS8_KEY_FILE% 的内容复制到 src\config.py 的 PRIVATE_KEY 字段
echo 2. 将 %PUBLIC_KEY_FILE% 的内容复制到 src\config.py 的 PUBLIC_KEY 字段
echo 3. 妥善保管私钥文件，不要泄露给他人
echo.
echo 安全提醒:
echo - 私钥文件包含敏感信息，请设置适当的文件权限
echo - 建议备份密钥文件到安全位置
echo - 生产环境中建议使用环境变量而非直接在代码中存储密钥
echo.
echo 文件已生成完成，按任意键退出...
pause >nul