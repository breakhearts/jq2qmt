# QMT-JQ 策略持仓管理系统
## 项目简介
这是一个用于聚宽(JoinQuant)和QMT(迅投QMT)之间持仓同步的系统。简单来说，就是让你在聚宽上运行的策略能够自动把持仓信息传递给QMT，实现两个平台之间的仓位同步。

## 项目结构和工作原理
### 项目结构
```
qmt_jq/
├── src/
│   ├── app.py                    # Flask服务器，提供API接口
│   ├── models/models.py          # 数据库模型，存储持仓信息
│   ├── api/
│   │   ├── jq_config.py        # 聚宽端配置文件（需要放到聚宽研究根目录）
│   │   ├── jq_qmt_api.py        # 聚宽端API，用于上传持仓（需要放到聚宽研究根目录）
│   │   └── qmt_jq_trade.py      # QMT端API，用于同步持仓（复制到QMT策略里执行）
│   └── templates/index.html     # 持仓查看页面
├── demo/多策略V1.0.py            # 聚宽策略示例
├── test_jq.py                   # 测试文件
└── requirements.txt             # 依赖包
```
### 工作原理
通俗解释 ：

1. 聚宽端 ：你的策略在聚宽平台运行，每次调仓后，策略会把最新的持仓信息（股票代码、数量、成本价）通过HTTP接口发送到你的服务器
2. 服务器端 ：Flask服务器接收持仓信息并存储到MySQL数据库中
3. QMT端 ：QMT客户端定期从服务器获取最新持仓信息，对比自己的实际持仓，然后通过买卖操作调整到目标仓位
数据流向 ：

```
聚宽策略 → HTTP请求 → Flask服务器 → MySQL数据库 → QMT客户端 → 实盘交易
```
## API接口说明
### 1. 更新策略持仓
- 接口 : POST /api/v1/positions/update
- 功能 : 聚宽策略调用此接口上传最新持仓
- 请求参数 :
```
{
  "strategy_name": "策略名称",
  "positions": [
    {
      "code": "000001.XSHE",
      "volume": 1000,
      "cost": 12.5
    }
  ]
}
```
### 2. 查询策略持仓
- 接口 : GET /api/v1/positions/strategy/<strategy_name>
- 功能 : 获取指定策略的持仓信息
- 返回示例 :
```
{
  "positions": [
    {
      "code": "000001.XSHE",
      "volume": 1000,
      "cost": 12.5,
      "update_time": "2024-01-01 10:30:00"
    }
  ]
}
```
### 3. 查询总持仓
- 接口 : GET /api/v1/positions/total
- 功能 : 获取所有策略的汇总持仓
## 使用方法
### jq_qmt_api.py 使用方法
这个文件是聚宽端使用的API客户端，用于向服务器上传持仓信息。

基本用法 ：

```
from jq_qmt_api import JQQMTAPI

# 初始化API客户端
api = JQQMTAPI()

# 准备持仓数据
positions = [
    {
        'code': '000001.XSHE',
        'volume': 1000,
        'cost': 12.5
    }
]

# 上传持仓
api.update_positions('我的策略', positions)
```
### 聚宽策略改写示例
基于你提供的 多策略V1.0.py ，以下是如何改写以保存最新持仓：

```
# 在文件开头导入API，并初始化API
from jq_qmt_api import JQQMTAPI
g.jq_qmt_api = JQQMTAPI()  # 初始化API客户端

# 增加save_all_positions函数
def save_all_positions(context):
    """保存所有策略的持仓信息到数据库"""
    if context.run_params.type != 'sim_trade':
        return
    
    # 收集当前所有持仓
    positions = []
    for code, pos in context.portfolio.positions.items():
        if pos.total_amount > 0:  # 只保存有持仓的股票
            positions.append({
                'code': pos.security,
                'volume': pos.total_amount,
                'cost': pos.avg_cost
            })
    
    try:
        # 上传到服务器
        g.jq_qmt_api.update_positions("多策略V1.0", positions)
        g.logger.info(f"持仓信息已保存: {len(positions)}只股票")
    except Exception as e:
        g.logger.warning(f"持仓更新失败: {str(e)}")

# 在每个调仓函数后调用save_all_positions
def all_day_adjust(context):
    g.strategys["全天候策略"].adjust()
    save_all_positions(context)  # 调仓后保存持仓

def simple_roa_adjust(context):
    g.strategys["简单ROA策略"].adjust()
    save_all_positions(context)  # 调仓后保存持仓

def wp_adjust(context):
    g.strategys["微盘"].adjust()
    save_all_positions(context)  # 调仓后保存持仓

# ... 其他调仓函数类似处理 ...
```
关键改动点 ：

1. 导入 JQQMTAPI 类
2. 在全局变量中初始化API客户端
3. 在每次调仓后调用 save_all_positions 函数
4. save_all_positions 函数收集当前持仓并上传到服务器
### qmt_jq_trade.py 使用方法
这个文件是QMT端使用的API客户端，用于从服务器获取持仓信息并执行交易。

基本用法 ：

```
from qmt_jq_trade import QMTAPI

# 初始化API客户端
api = QMTAPI(C, strategy_names=['多策略V1.0'])   # 这里指定你自己的策略名称

# 获取服务器上的持仓信息
server_positions = api.get_total_positions()

# 对比并同步持仓
# (具体的交易逻辑需要结合QMT的交易API实现)
```
## 配置说明
### 1. 服务器配置
将 src/config_template.py 文件重命名为 config.py 并修改配置：


```
# 数据库配置
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': '127.0.0.1',
    'username': 'username',         # 替换成你的数据库用户名
    'password': 'password',         # 替换成你的数据库密码
    'database': 'quant',
    'port': 3306
}
```
### 2. API地址配置
在 jq_config.py 和 qmt_jq_trade.py 中修改：

```
API_URL = "http://你的服务器IP:端口"  # 例如: http://123.456.789.0:5366
```
## 快速开始

1. 克隆项目
```bash
git clone <repository-url>
cd jq2qmt
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 生成密钥对
```bash
# Linux/macOS
./generate_keys.sh

# Windows
generate_keys.bat
```

4. 配置数据库和API设置
```bash
cp src/config_template.py src/config.py
# 编辑 src/config.py 配置文件
# 将生成的密钥内容复制到配置文件中
```

5. 运行应用
```bash
python src/app.py
```

## 详细文档

### 📖 API使用指南
详细的API接口使用说明请参考：[API_USAGE.md](API_USAGE.md)

该文档包含：
- 完整的API接口说明
- 认证机制详解（加密认证和简单认证）
- 客户端使用示例
- 安全建议和最佳实践
- 错误处理和故障排除

### 🔐 密钥生成指南
密钥对生成的详细说明请参考：[KEYGEN_README.md](KEYGEN_README.md)

该文档包含：
- 密钥生成工具使用方法
- 跨平台支持（Linux/macOS/Windows）
- 密钥格式说明（PKCS#8和X.509）
- 安全配置建议
- 故障排除指南

## 部署步骤
1. 安装依赖 ：
```
pip install -r requirements.txt
```
2. 配置数据库 ：
- 安装MySQL
- 创建数据库和用户
- 配置 config.py
3. 启动服务 ：
```
cd src
python app.py
```
4. 测试接口 ：
```
python test_jq.py
```
## 注意事项
1. 网络连接 ：确保聚宽和QMT都能访问你的服务器
2. 数据安全 ：生产环境建议使用HTTPS和数据库密码保护
3. 错误处理 ：策略中要做好异常处理，避免因网络问题影响策略运行
4. 频率控制 ：不要过于频繁地调用API，建议只在调仓时调用
通过这个系统，你就可以实现聚宽策略和QMT实盘的自动同步了！