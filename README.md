# JQ2QMT 持仓同步系统

## 项目简介
这是一个用于聚宽(JoinQuant)和QMT(迅投QMT)之间持仓同步的系统。简单来说，就是让你在聚宽上运行的策略能够自动把持仓信息传递给QMT，实现两个平台之间的仓位同步。

### ✨ 特色功能
- 🚀 **一键初始化**：使用 `init_project.py` 脚本，引导式配置所有必要参数
- 🔐 **双重认证**：支持RSA加密认证和简单密码认证两种方式
- 📊 **可视化管理**：Web界面查看持仓、手动调整仓位
- 🛡️ **安全可靠**：密码加密存储，支持端口自适应配置
- 👥 **用户管理系统**：完整的用户登录、权限管理和超级管理员功能
- 📊 **跟单比例配置**：支持按比例跟单交易，股数自动调整为100倍数
- 🔑 **私钥数据库存储**：用户私钥安全存储在数据库中，支持密钥验证

## 项目结构和工作原理
### 项目结构
```
qmt_jq/
├── init_project.py              # 🚀 一键初始化脚本（推荐使用）
├── src/
│   ├── app.py                    # Flask服务器，提供API接口
│   ├── config_template.py        # 配置文件模板
│   ├── models/models.py          # 数据库模型，存储持仓信息和用户数据
│   ├── api/
│   │   ├── jq_config.py        # 聚宽端配置文件（需要放到聚宽研究根目录）
│   │   ├── jq_qmt_api.py        # 聚宽端API，用于上传持仓（需要放到聚宽研究根目录）
│   │   └── qmt_jq_trade.py      # QMT端API，用于同步持仓（复制到QMT策略里执行,需要手动编辑编辑账号和密码）
│   ├── auth/
│   │   └── simple_crypto_auth.py # 加密认证系统
│   └── templates/
│       ├── index.html           # 持仓查看页面
│       ├── adjustment.html      # 持仓调整页面
│       ├── password.html        # 密码管理页面
│       ├── login.html           # 用户登录页面
│       └── user_management.html # 用户管理页面（超级管理员专用）
├── demo/多策略V1.0.py            # 聚宽策略示例
├── test_jq.py                   # 测试文件
├── generate_keys.sh             # Linux/macOS密钥生成脚本
├── generate_keys.bat            # Windows密钥生成脚本
└── requirements.txt             # 依赖包
```
### 工作原理
通俗解释 ：

1. 聚宽端 ：你的策略在聚宽平台运行，每次调仓后，策略会把最新的持仓信息（股票代码、数量、成本价）通过HTTP接口发送到你的服务器
2. 服务器端 ：Flask服务器接收持仓信息并存储到MySQL数据库中
3. QMT端 ：QMT客户端定期从服务器获取最新持仓信息，对比自己的实际持仓，然后通过买卖操作调整到目标仓位
数据流向 ：

```
聚宽策略 → HTTP请求 → Flask服务器 → MySQL数据库 → QMT客户端 → 实盘交易
```

## V1.2 新增功能

### 👥 完整用户管理系统
系统新增了完整的用户认证和管理功能：

- **用户登录系统**: 支持用户名/密码登录，会话管理
- **权限管理**: 区分普通用户和超级管理员权限
- **私钥存储**: 用户私钥安全存储在数据库中
- **超级管理员功能**: 用户管理、查看活跃状态、创建删除用户
- **默认账户**: 系统自动创建默认超级管理员 `admin/admin123`

### 📊 跟单比例配置
新增智能跟单比例功能：

- **比例设置**: 初始化时可配置账户跟单比例（如0.5表示使用50%资金）
- **自动调整**: 交易数量自动调整为100股的倍数
- **灵活配置**: 支持0.1-1.0之间任意比例，适应不同风险偏好

### 🔐 安全性增强
- **数据库存储**: 用户密钥和认证信息安全存储
- **会话管理**: 支持Flask-Login或Session认证
- **权限控制**: 页面级别的权限验证
- **活跃监控**: 自动记录用户登录和活跃时间

## V1.1 新增功能

### 🔐 密码管理系统
系统新增了内部密码管理功能，提供了更便捷的认证方式：

- **密码管理页面** : 访问 `/password` 可以查看和修改内部密码
- **内部API认证** : 新增 `/api/v1/positions/update/internal` 接口，使用密码认证替代RSA令牌
- **持仓调整页面** : 访问 `/adjustment` 可以手动调整持仓，支持密码认证保存
- **安全特性** : 密码使用bcrypt加密存储，支持密码强度验证

### 🎯 持仓调整功能
新增了可视化的持仓调整界面：

- **实时编辑** : 支持添加、修改、删除持仓调整项
- **数据持久化** : 调整数据自动保存到数据库
- **用户友好** : 提供直观的表格界面和模态框操作
- **数据验证** : 前端和后端双重数据验证

## API接口说明

### 0. 用户认证接口

#### 0.1 用户登录
- 页面: `/login`
- 功能: 用户登录界面，支持用户名/密码认证
- 特性: 支持"记住我"功能（7天有效期）

#### 0.2 用户管理（仅超级管理员）
- 页面: `/users`
- 功能: 用户管理界面，查看所有用户、创建删除用户
- 接口: 
  - `POST /users/create` - 创建新用户
  - `POST /users/delete` - 删除用户

### 1. 更新策略持仓
- 接口 : POST /api/v1/positions/update
- 功能 : 聚宽策略调用此接口上传最新持仓（需要RSA加密认证）
- 请求参数 :
```
{
  "strategy_name": "策略名称",
  "positions": [
    {
      "code": "000001.XSHE",
      "volume": 1000,
      "cost": 12.5
    }
  ]
}
```

### 1.1 内部更新策略持仓
- 接口 : POST /api/v1/positions/update/internal
- 功能 : 内部使用的持仓更新接口,更新持仓网页使用（使用密码认证，无需RSA令牌）
- 请求参数 :
```
{
  "password": "内部密码",
  "strategy_name": "策略名称",
  "positions": [
    {
      "code": "000001.XSHE",
      "volume": 1000,
      "cost": 12.5
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
  "positions": [
    {
      "code": "000001.XSHE",
      "volume": 1000,
      "cost": 12.5,
      "update_time": "2024-01-01 10:30:00"
    }
  ]
}
```

### 3. 查询总持仓
- 接口 : GET /api/v1/positions/total
- 功能 : 获取所有策略的汇总持仓

### 4. 密码管理接口
#### 4.1 获取密码信息
- 接口 : GET /api/v1/internal/password/info
- 功能 : 获取当前内部密码状态信息
- 返回示例 :
```
{
  "is_default": false,
  "created_at": "2024-01-01 10:00:00",
  "updated_at": "2024-01-01 12:00:00"
}
```

#### 4.2 设置密码
- 接口 : POST /api/v1/internal/password/set
- 功能 : 设置或修改内部密码
- 请求参数 :
```
{
  "current_password": "当前密码",
  "new_password": "新密码"
}
```

## 使用方法
### jq_qmt_api.py 使用方法
这个文件是聚宽端使用的API客户端，用于向服务器上传持仓信息。

基本用法 ：

```
from jq_qmt_api import JQQMTAPI

# 初始化API客户端
api = JQQMTAPI()

# 准备持仓数据
positions = [
    {
        'code': '000001.XSHE',
        'volume': 1000,
        'cost': 12.5
    }
]

# 上传持仓
api.update_positions('我的策略', positions)
```
### 聚宽策略改写示例
基于你提供的 多策略V1.0.py ，以下是如何改写以保存最新持仓：

```
# 在文件开头导入API，并初始化API
from jq_qmt_api import JQQMTAPI
g.jq_qmt_api = JQQMTAPI()  # 初始化API客户端

# 增加save_all_positions函数
def save_all_positions(context):
    """保存所有策略的持仓信息到数据库"""
    if context.run_params.type != 'sim_trade':
        return
    
    # 收集当前所有持仓
    positions = []
    for code, pos in context.portfolio.positions.items():
        if pos.total_amount > 0:  # 只保存有持仓的股票
            positions.append({
                'code': pos.security,
                'volume': pos.total_amount,
                'cost': pos.avg_cost
            })
    
    try:
        # 上传到服务器
        g.jq_qmt_api.update_positions("多策略V1.0", positions)
        g.logger.info(f"持仓信息已保存: {len(positions)}只股票")
    except Exception as e:
        g.logger.warning(f"持仓更新失败: {str(e)}")

# 在每个调仓函数后调用save_all_positions
def all_day_adjust(context):
    #g.strategys["全天候策略"].adjust() 示例
    save_all_positions(context)  # 调仓后保存持仓

def simple_roa_adjust(context):
    #g.strategys["简单ROA策略"].adjust() 示例
    save_all_positions(context)  # 调仓后保存持仓

def wp_adjust(context):
    #g.strategys["微盘"].adjust() 示例
    save_all_positions(context)  # 调仓后保存持仓

# ... 其他调仓函数类似处理 ...
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
from qmt_jq_trade import QMTAPI

# 初始化API客户端
api = QMTAPI(C, strategy_names=['多策略V1.0'])   # 这里指定你自己的策略名称

# 获取服务器上的持仓信息
server_positions = api.get_total_positions()

# 对比并同步持仓
# (具体的交易逻辑需要结合QMT的交易API实现)
```
## 配置说明

### 🚀 推荐方式：使用初始化脚本

**强烈推荐使用 `init_project.py` 进行引导式配置**，脚本会逐步引导您完成所有必要的配置：

```bash
python init_project.py
```

初始化脚本会依次配置以下内容：

#### 1. 数据库配置
脚本会提示您输入以下数据库信息：
- **数据库主机地址**：默认 `localhost`，如果数据库在其他服务器请输入相应IP
- **数据库端口**：默认 `3306`，MySQL标准端口
- **数据库用户名**：您的MySQL用户名
- **数据库密码**：您的MySQL密码
- **数据库名称**：默认 `quant`，用于存储持仓数据的数据库

#### 2. API服务配置
脚本会自动配置API服务参数：
- **服务主机地址**：默认 `0.0.0.0`（监听所有网络接口）
- **服务端口**：默认 `5366`（Flask应用监听端口）

#### 3. 外部访问配置
**重要**：您需要提供以下信息：
- **服务器IP地址**：您的服务器公网IP或内网IP（必填）
- **外部访问端口**：默认 `80`，聚宽和QMT访问您服务器的端口

#### 4. 跟单模式配置
**新功能**：配置跟单比例：
- **跟单比例**：设置账户总资产用于跟单的比例（0.1-1.0）
- **自动调整**：交易数量自动调整为100股的倍数
- **风险控制**：可根据风险偏好设置不同比例

#### 5. 加密认证配置
脚本会自动：
- 生成RSA密钥对（用于聚宽端安全认证）
- 配置加密认证参数
- 设置简单API密钥（用于内部管理）

#### 6. 自动生成的文件
初始化完成后，脚本会自动生成：
- `src/config.py` - 主配置文件（包含跟单比例配置）
- `src/api/jq_config.py` - 聚宽端配置文件（包含跟单比例）
- `src/api/qmt_jq_trade.py` - QMT端配置文件（已更新API_URL和跟单逻辑）
- `quant_id_rsa_pkcs8.pem` - RSA私钥文件
- `quant_id_rsa_public.pem` - RSA公钥文件

#### 7. 用户系统初始化
脚本会自动创建：
- 用户数据库表结构
- 默认超级管理员账户（admin/admin123）
- 用户认证和权限系统

### 📝 手动配置方式（不推荐）

如果您需要手动配置，可以参考以下步骤：

#### 1. 服务器配置
将 `src/config_template.py` 文件重命名为 `config.py` 并修改配置：

```python
# 数据库配置
DB_CONFIG = {
    'drivername': 'mysql+pymysql',
    'host': '127.0.0.1',           # 数据库主机地址
    'username': 'username',         # 替换成你的数据库用户名
    'password': 'password',         # 替换成你的数据库密码
    'database': 'quant',           # 数据库名称
    'port': 3306                   # 数据库端口
}
```

#### 2. API地址配置
在 `jq_config.py` 和 `qmt_jq_trade.py` 中修改：

```python
API_URL = "http://你的服务器IP:端口"  # 例如: http://123.456.789.0:5366
```

**注意**：如果使用80端口，URL中不需要包含端口号：
- 80端口：`http://123.456.789.0`
- 其他端口：`http://123.456.789.0:5366`
## 快速开始

### 🚀 一键配置（推荐）

1. 克隆项目
```bash
git clone <repository-url>
cd jq2qmt
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行初始化脚本（一键配置）
```bash
python init_project.py
```

**初始化脚本会自动完成以下操作：**
- ✅ 生成RSA密钥对
- ✅ 配置数据库连接信息
- ✅ 设置API服务参数
- ✅ 配置外部访问地址
- ✅ 生成所有必要的配置文件
- ✅ 验证配置正确性

**您只需要准备：**
- MySQL数据库的连接信息（主机、用户名、密码等）
- 服务器的IP地址（用于外部访问）

4. 运行应用
```bash
python src/app.py
```

5. 首次登录
```bash
# 访问登录页面
浏览器打开: http://localhost:5366/login
# 使用默认账户登录
用户名: admin
密码: admin123
```

**⚠️ 安全提醒**: 首次登录后请立即修改默认密码！

## 详细文档

### 📖 用户管理系统指南
完整的用户管理功能说明请参考：[USER_MANAGEMENT_README.md](USER_MANAGEMENT_README.md)

该文档包含：
- 用户认证系统详解
- 权限管理和超级管理员功能
- 私钥存储和安全机制
- 用户管理界面使用指南
- 安全配置和最佳实践

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

### 🔒 内部API使用指南
内部API的详细使用说明请参考：[INTERNAL_API_README.md](INTERNAL_API_README.md)

该文档包含：
- 内部密码管理系统说明
- 密码认证API使用方法
- 持仓调整功能使用指南
- 安全配置和最佳实践

## 部署步骤
1. 安装依赖 ：
```
pip install -r requirements.txt
```
2. 配置数据库 ：
- 安装MySQL
- 创建数据库和用户
- 运行初始化脚本或手动配置 config.py

3. 初始化用户系统 ：
```
python update_database_for_users.py
```

4. 启动服务 ：
```
cd src
python app.py
```

5. 访问系统 ：
```
浏览器访问: http://localhost:5366/login
默认账户: admin / admin123
```

6. 测试接口 ：
```
python test_jq.py
```
## 注意事项
1. **网络连接** ：确保聚宽和QMT都能访问你的服务器
2. **数据安全** ：生产环境建议使用HTTPS和数据库密码保护
3. **错误处理** ：策略中要做好异常处理，避免因网络问题影响策略运行
4. **频率控制** ：不要过于频繁地调用API，建议只在调仓时调用
5. **密码安全** ：内部密码请设置足够复杂，定期更换，避免使用默认密码
6. **权限管理** ：内部API仅用于可信环境，不要暴露给外部网络
7. **用户安全** ：首次部署后立即修改默认管理员密码
8. **跟单比例** ：根据实际资金情况合理设置跟单比例，注意风险控制
9. **股数限制** ：系统自动将交易数量调整为100股倍数，小额持仓可能被忽略

## 使用建议

### 认证方式选择
- **RSA加密认证** : 适用于聚宽等外部平台调用，安全性更高
- **密码认证** : 适用于内部管理和手动操作，使用更便捷
- **Web界面** : 适用于日常监控和手动调整持仓
- **用户系统** : 多人使用时的权限管理和安全控制

### 工作流程建议
1. 使用聚宽策略自动上传持仓（RSA认证）
2. 通过Web界面监控持仓状态（需要登录）
3. 必要时使用调整页面手动修改持仓（密码认证）
4. 定期通过密码管理页面更新内部密码
5. 超级管理员定期检查用户活跃状态和权限
6. 根据实际情况调整跟单比例配置

### 安全建议
1. **定期更换密码** ：建议每月更换用户密码和内部密码
2. **权限最小化** ：只给必要的用户超级管理员权限
3. **监控用户活动** ：定期检查用户登录和活跃记录
4. **备份数据** ：定期备份数据库中的用户和持仓数据
5. **网络安全** ：生产环境建议使用HTTPS和防火墙保护

通过这个系统，你就可以实现聚宽策略和QMT实盘的自动同步了！

## 更新日志

### V2.0 (2025-07-19)
- ✅ 新增完整用户管理系统
  - 用户登录认证（用户名/密码）
  - 权限管理（普通用户/超级管理员）
  - 用户活跃状态监控
  - 默认超级管理员账户（admin/admin123）
- ✅ 私钥数据库存储
  - 用户私钥安全存储在数据库
  - 支持密钥验证和更新
- ✅ 跟单比例配置功能
  - 初始化时可配置跟单比例（0.1-1.0）
  - 交易数量自动调整为100股倍数
  - 支持风险控制和资金管理
- ✅ 超级管理员功能
  - 用户管理界面
  - 查看用户活跃状态
  - 创建和删除用户
- ✅ 安全性增强
  - 页面级别权限验证
  - 会话管理和自动过期
  - 防止权限提升攻击

### V1.1 (2024-07-19)
- ✅ 密码管理系统
- ✅ 持仓调整功能
- ✅ 内部API认证
- ✅ Web界面优化

### V1.0 (2024-07-19)
- ✅ 基础持仓同步功能
- ✅ RSA加密认证
- ✅ 数据库存储
- ✅ 基础Web界面