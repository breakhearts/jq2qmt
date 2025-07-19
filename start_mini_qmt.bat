@echo off
chcp 65001 >nul
echo ===========================================
echo         Mini QMT Trade 启动脚本
echo ===========================================
echo.

echo 请选择运行模式:
echo 1. 实盘模式 (默认)
echo 2. 模拟模式
echo 3. Redis连接测试
echo 4. 单次同步测试
echo 5. 指定策略运行
echo.

set /p choice="请输入选项 (1-5, 默认1): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo 启动实盘交易模式...
    python run_mini_qmt_trade.py
) else if "%choice%"=="2" (
    echo 启动模拟交易模式...
    python run_mini_qmt_trade.py --simulation
) else if "%choice%"=="3" (
    echo 测试Redis连接...
    python run_mini_qmt_trade.py --test-redis
) else if "%choice%"=="4" (
    echo 执行单次同步测试...
    python run_mini_qmt_trade.py --sync-once --simulation
) else if "%choice%"=="5" (
    echo 指定策略运行 (hand_strategy)...
    python run_mini_qmt_trade.py --simulation --strategies hand_strategy
) else (
    echo 无效选项，使用默认实盘模式...
    python run_mini_qmt_trade.py
)

echo.
echo 程序已退出
pause
