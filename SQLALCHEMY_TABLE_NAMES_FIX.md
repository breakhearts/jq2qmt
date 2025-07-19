# SQLAlchemy table_names() 方法修复

## 问题描述

在运行 `init_project.py` 时遇到错误：
```
2025-07-19 16:44:08,580 - ERROR - 验证数据库失败: 'Engine' object has no attribute 'table_names'
```

## 原因分析

这个错误是由于SQLAlchemy版本更新导致的：
- 在较旧的SQLAlchemy版本中，可以使用 `engine.table_names()` 方法获取数据库中的表名
- 在新版本的SQLAlchemy中，这个方法已被移除
- 需要使用 `sqlalchemy.inspect()` 模块来获取表信息

## 修复方案

### 1. 修改 `init_database.py`

#### 添加导入
```python
from sqlalchemy import create_engine, text, inspect
```

#### 修改表检查逻辑
```python
# 旧代码（已失效）
tables = db.engine.table_names()

# 新代码（修复后）
inspector = inspect(db.engine)
tables = inspector.get_table_names()
```

### 2. 修改 `setup_database.py`

#### 添加导入
```python
from sqlalchemy import inspect
```

#### 取消注释并修复表检查代码
```python
# 旧代码（注释掉的）
#tables = db.engine.table_names()
#print(f"✓ 已创建的表: {', '.join(tables)}")

# 新代码（修复后）
inspector = inspect(db.engine)
tables = inspector.get_table_names()
print(f"✓ 已创建的表: {', '.join(tables)}")
```

## 修改的文件

1. **`init_database.py`**
   - 添加 `inspect` 导入
   - 修改 `verify_database()` 函数中的表检查逻辑

2. **`setup_database.py`**
   - 添加 `inspect` 导入
   - 启用并修复表检查代码

3. **`test_database_inspect.py`** (新增)
   - 创建测试脚本验证修复是否正确

## 兼容性

这个修复方案：
- ✅ 兼容新版本的SQLAlchemy (1.4+, 2.0+)
- ✅ 向后兼容较旧版本的SQLAlchemy
- ✅ 不影响现有功能
- ✅ 保持相同的API行为

## 测试验证

可以运行以下命令测试修复是否成功：

```bash
# 测试表检查功能
python test_database_inspect.py

# 运行完整的项目初始化
python init_project.py

# 运行数据库设置
python setup_database.py
```

## 相关SQLAlchemy版本变更

- **SQLAlchemy 1.4+**: `engine.table_names()` 被标记为已弃用
- **SQLAlchemy 2.0+**: `engine.table_names()` 完全移除
- **推荐方式**: 使用 `inspect(engine).get_table_names()`

## 其他可能的相关方法

如果项目中还使用了其他已弃用的方法，可能需要类似的修复：

```python
# 获取表名
inspector = inspect(engine)
table_names = inspector.get_table_names()

# 获取列信息
columns = inspector.get_columns('table_name')

# 获取索引信息
indexes = inspector.get_indexes('table_name')

# 获取外键信息
foreign_keys = inspector.get_foreign_keys('table_name')
```

## 总结

通过使用现代的SQLAlchemy `inspect` 接口，成功解决了 `table_names()` 方法不存在的问题。这个修复确保了项目与新版本SQLAlchemy的兼容性，同时保持了代码的清晰性和可维护性。
