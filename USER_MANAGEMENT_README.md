# JQ-QMT 用户管理系统

## 概述

JQ-QMT 系统现在支持完整的用户管理功能，包括用户登录验证、权限管理、私钥存储和超级管理员功能。

## 功能特性

### 1. 用户认证
- 用户名/密码登录
- 会话管理（支持"记住我"功能）
- 自动登录状态检查
- 安全的密码哈希存储（SHA256）

### 2. 权限管理
- **普通用户**: 可以查看持仓、调整持仓、管理密码
- **超级管理员**: 拥有所有普通用户权限，额外可以管理用户

### 3. 私钥管理
- 用户私钥/公钥存储在数据库中
- 支持密钥验证和更新
- 安全的密钥存储机制

### 4. 超级管理员功能
- 查看所有用户信息
- 创建新用户
- 删除用户（禁用账户）
- 查看用户活跃状态和登录统计

## 默认账户

系统初始化时会自动创建默认超级管理员账户：
- **用户名**: `admin`
- **密码**: `admin123`
- **权限**: 超级管理员

## 页面说明

### 登录页面 (`/login`)
- 用户名/密码登录
- 记住我功能（7天有效）
- 友好的错误提示

### 用户管理页面 (`/users`) - 仅超级管理员
- 用户列表展示
- 用户统计信息
- 创建新用户
- 删除用户功能
- 查看用户活跃状态

### 主要功能页面
- `/` - 持仓查看页面（需要登录）
- `/adjustment` - 持仓调整页面（需要登录）
- `/password` - 密码管理页面（需要登录）

## 数据库结构

### 用户表 (`users`)
```sql
CREATE TABLE `users` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `username` varchar(80) NOT NULL,
    `password_hash` varchar(64) NOT NULL,
    `private_key` text DEFAULT NULL,
    `public_key` text DEFAULT NULL,
    `is_superuser` tinyint(1) NOT NULL DEFAULT 0,
    `is_active` tinyint(1) NOT NULL DEFAULT 1,
    `created_time` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `last_login_time` datetime DEFAULT NULL,
    `last_activity_time` datetime DEFAULT NULL,
    `login_count` int(11) NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`)
);
```

## 安装和部署

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 更新数据库
```bash
# 运行数据库更新脚本
python update_database_for_users.py

# 或者手动执行SQL
mysql -u username -p database_name < database_schema.sql
```

### 3. 启动应用
```bash
cd src
python app.py
```

### 4. 访问系统
- 打开浏览器访问: `http://localhost:5366/login`
- 使用默认账户登录: `admin` / `admin123`

## API变化

所有Web页面现在都需要登录验证：
- 未登录用户会被重定向到登录页面
- 用户活跃时间会自动更新
- 超级管理员专用页面有额外权限检查

## 安全特性

### 1. 密码安全
- 使用SHA256哈希存储密码
- 不存储明文密码
- 登录失败提示信息安全

### 2. 会话安全
- 安全的会话密钥
- 会话过期管理
- 支持Flask-Login（如果安装）或Session回退

### 3. 权限控制
- 基于用户角色的访问控制
- 超级管理员权限隔离
- 防止权限提升攻击

## 配置说明

### 跟单比例支持
系统现在支持跟单比例配置（在配置文件中）：
```python
# 跟单模式配置
FOLLOW_TRADING_CONFIG = {
    'RATIO': 0.5  # 账户跟单比例
}
```

### Redis缓存
用户信息会缓存在Redis中以提高性能：
- 用户基本信息缓存
- 自动缓存失效机制
- 降低数据库查询压力

## 故障排除

### 1. 登录问题
- 确认用户名/密码正确
- 检查数据库连接
- 查看应用日志

### 2. 权限问题
- 确认用户权限级别
- 检查is_superuser字段
- 验证用户激活状态

### 3. 数据库问题
- 运行 `update_database_for_users.py`
- 手动执行 `database_schema.sql`
- 检查表结构是否正确

## 开发注意事项

### 1. 添加新页面
使用装饰器保护页面：
```python
@app.route('/new_page')
@web_login_required  # 需要登录
def new_page():
    return render_template('new_page.html')

@app.route('/admin_page')
@superuser_required  # 需要超级管理员
def admin_page():
    return render_template('admin_page.html')
```

### 2. 模板中获取用户信息
```html
<!-- 检查用户权限 -->
{% if session.is_superuser or (current_user and current_user.is_superuser) %}
    <a href="/admin">管理页面</a>
{% endif %}

<!-- 显示用户名 -->
<span>欢迎，{{ session.user_id or (current_user.username if current_user else 'Unknown') }}！</span>
```

### 3. 用户活跃时间
系统会自动更新用户活跃时间，超级管理员可以查看用户活跃状态。

## 更新日志

- ✅ 添加用户认证系统
- ✅ 实现权限管理
- ✅ 私钥数据库存储
- ✅ 超级管理员功能
- ✅ 登录页面和用户管理界面
- ✅ Redis缓存支持
- ✅ 会话管理和安全性
- ✅ 数据库架构更新
