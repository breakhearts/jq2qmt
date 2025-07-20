#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
包含建库建表语句和数据初始化
"""

import os
import sys
import logging
from datetime import datetime
import pymysql
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import URL

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DB_CONFIG, SQLALCHEMY_DATABASE_URI
from src.models.models import db, StrategyPosition, InternalPasswordManager, User, UserStrategy

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database():
    """创建数据库（如果不存在）"""
    try:
        # 连接MySQL服务器（不指定数据库）
        server_config = DB_CONFIG.copy()
        database_name = server_config.pop('database')
        
        server_url = URL.create(**server_config)
        engine = create_engine(server_url)
        
        with engine.connect() as connection:
            # 检查数据库是否存在
            result = connection.execute(text(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"
            ), {"db_name": database_name})
            
            if result.fetchone():
                logger.info(f"数据库 {database_name} 已存在")
            else:
                # 创建数据库
                connection.execute(text(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                connection.commit()
                logger.info(f"数据库 {database_name} 创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        return False

def get_create_table_sql():
    """获取建表SQL语句"""
    
    # 策略持仓表
    strategy_positions_sql = """
    CREATE TABLE IF NOT EXISTS `strategy_positions` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `strategy_name` varchar(100) NOT NULL COMMENT '策略名称',
        `positions` json NOT NULL COMMENT '持仓数据JSON',
        `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_strategy_name` (`strategy_name`),
        KEY `idx_strategy_name` (`strategy_name`),
        KEY `idx_update_time` (`update_time`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='策略持仓表';
    """
    
    # 内部密码表
    internal_passwords_sql = """
    CREATE TABLE IF NOT EXISTS `internal_passwords` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `password_hash` varchar(64) NOT NULL COMMENT '密码哈希值',
        `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内部密码表';
    """
    
    # 用户表
    users_sql = """
    CREATE TABLE IF NOT EXISTS `users` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `username` varchar(80) NOT NULL COMMENT '用户名',
        `password_hash` varchar(64) NOT NULL COMMENT '密码哈希值',
        `private_key` text DEFAULT NULL COMMENT '用户私钥(PEM格式)',
        `public_key` text DEFAULT NULL COMMENT '用户公钥(PEM格式)',
        `is_superuser` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为超级管理员',
        `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '账户是否激活',
        `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        `last_login_time` datetime DEFAULT NULL COMMENT '最后登录时间',
        `last_activity_time` datetime DEFAULT NULL COMMENT '最后活跃时间',
        `login_count` int(11) NOT NULL DEFAULT 0 COMMENT '登录次数',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_username` (`username`),
        KEY `idx_username` (`username`),
        KEY `idx_is_active` (`is_active`),
        KEY `idx_last_activity_time` (`last_activity_time`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
    """
    
    return [strategy_positions_sql, internal_passwords_sql, users_sql]

def create_tables_with_sql():
    """使用原生SQL创建表"""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as connection:
            # 执行建表语句
            for sql in get_create_table_sql():
                connection.execute(text(sql))
                connection.commit()
                
            logger.info("使用SQL语句创建表结构成功")
        
        return True
        
    except Exception as e:
        logger.error(f"使用SQL创建表失败: {e}")
        return False

def create_tables_with_sqlalchemy():
    """使用SQLAlchemy创建表"""
    try:
        from flask import Flask
        
        # 创建Flask应用上下文
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # 创建所有表
            db.create_all()
            logger.info("使用SQLAlchemy创建表结构成功")
        
        return True
        
    except Exception as e:
        logger.error(f"使用SQLAlchemy创建表失败: {e}")
        return False

def init_default_data():
    """初始化默认数据"""
    try:
        from flask import Flask
        
        # 创建Flask应用上下文
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # 检查是否已有管理员用户（内部密码现在使用管理员密码）
            admin_user = InternalPasswordManager.get_admin_user()
            if not admin_user:
                logger.info("尚无管理员用户，将在create_admin_user函数中创建")
            else:
                logger.info(f"管理员用户已存在: {admin_user.username}")
            
            # 创建示例策略（可选）
            if not StrategyPosition.query.filter_by(strategy_name='example_strategy').first():
                example_positions = [
                    {
                        'code': '000001.SZ',
                        'name': '平安银行',
                        'volume': 100,
                        'cost': 12.50
                    },
                    {
                        'code': '600000.SH', 
                        'name': '浦发银行',
                        'volume': 200,
                        'cost': 8.20
                    }
                ]
                
                StrategyPosition.update_positions('example_strategy', example_positions)
                logger.info("已创建示例策略数据")
            else:
                logger.info("示例策略已存在，跳过创建")
        
        return True
        
    except Exception as e:
        logger.error(f"初始化默认数据失败: {e}")
        return False

def create_admin_user(username="admin", password="admin123", private_key_pem=None, public_key_pem=None):
    """创建初始管理员用户"""
    try:
        from flask import Flask
        
        # 创建Flask应用上下文
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # 导入User模型
            from src.models.models import User
            
            # 检查管理员用户是否已存在
            existing_admin = User.query.filter_by(username=username).first()
            if existing_admin:
                # 更新现有管理员的密钥
                if private_key_pem and public_key_pem:
                    existing_admin.private_key = private_key_pem
                    existing_admin.public_key = public_key_pem
                    existing_admin.updated_time = datetime.now()
                    db.session.commit()
                    logger.info(f"已更新管理员用户 {username} 的密钥")
                else:
                    logger.info(f"管理员用户 {username} 已存在，跳过创建")
                return True
            
            # 创建新的管理员用户
            admin_user = User.create_user(
                username=username,
                password=password,
                private_key=private_key_pem,
                public_key=public_key_pem,
                is_superuser=True
            )
            
            logger.info(f"已创建初始管理员用户: {username}")
            if private_key_pem and public_key_pem:
                logger.info("管理员密钥已设置")
            
        return True
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        return False

def verify_database():
    """验证数据库结构和数据"""
    try:
        from flask import Flask
        
        # 创建Flask应用上下文
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # 检查表是否存在 - 使用现代SQLAlchemy方法
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            required_tables = ['strategy_positions', 'internal_passwords', 'users']
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                logger.error(f"缺少数据表: {missing_tables}")
                return False
            
            logger.info(f"数据表验证成功: {tables}")
            
            # 检查数据
            strategy_count = StrategyPosition.query.count()
            
            # 检查用户表
            try:
                user_count = User.query.count()
                admin_count = User.query.filter_by(is_superuser=True).count()
                logger.info(f"用户数量: {user_count}")
                logger.info(f"管理员数量: {admin_count}")
            except Exception as e:
                logger.warning(f"无法检查用户数量: {e}")
            
            logger.info(f"策略数量: {strategy_count}")
            
            # 测试密码验证（现在使用管理员密码）
            if InternalPasswordManager.verify_password("admin123"):
                logger.info("默认密码验证成功")
            else:
                logger.warning("默认密码验证失败")
        
        return True
        
    except Exception as e:
        logger.error(f"验证数据库失败: {e}")
        return False

def export_database_schema():
    """导出数据库结构为SQL文件"""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        
        # 生成建表SQL
        schema_sql = []
        schema_sql.append("-- JQ-QMT 数据库结构")
        schema_sql.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        schema_sql.append("")
        
        # 添加建库语句
        schema_sql.append(f"-- 创建数据库")
        schema_sql.append(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        schema_sql.append(f"USE `{DB_CONFIG['database']}`;")
        schema_sql.append("")
        
        # 添加建表语句
        for sql in get_create_table_sql():
            schema_sql.append(sql)
            schema_sql.append("")
        
        # 添加默认数据
        schema_sql.append("-- 默认数据")
        schema_sql.append("INSERT IGNORE INTO `internal_passwords` (`password_hash`, `created_time`, `updated_time`) VALUES")
        schema_sql.append("(SHA2('admin123', 256), NOW(), NOW());")
        schema_sql.append("")
        schema_sql.append("-- 创建默认管理员用户（密码: admin123）")
        schema_sql.append("INSERT IGNORE INTO `users` (`username`, `password_hash`, `is_superuser`, `is_active`, `created_time`, `updated_time`) VALUES")
        schema_sql.append("('admin', SHA2('admin123', 256), 1, 1, NOW(), NOW());")
        schema_sql.append("")
        
        # 写入文件
        schema_file = 'database_schema.sql'
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(schema_sql))
        
        logger.info(f"数据库结构已导出到: {schema_file}")
        return True
        
    except Exception as e:
        logger.error(f"导出数据库结构失败: {e}")
        return False

def main():
    """主初始化流程"""
    print("=" * 60)
    print("JQ-QMT 数据库初始化")
    print("=" * 60)
    
    # 1. 创建数据库
    print("\n1. 创建数据库...")
    if not create_database():
        print("❌ 数据库创建失败")
        return False
    
    # 2. 创建表结构（优先使用SQL，失败时使用SQLAlchemy）
    print("\n2. 创建表结构...")
    if not create_tables_with_sql():
        print("⚠️  SQL方式创建表失败，尝试SQLAlchemy方式...")
        if not create_tables_with_sqlalchemy():
            print("❌ 表结构创建失败")
            return False
    
    # 3. 初始化默认数据
    print("\n3. 初始化默认数据...")
    if not init_default_data():
        print("❌ 默认数据初始化失败")
        return False
    
    # 4. 验证数据库
    print("\n4. 验证数据库...")
    if not verify_database():
        print("❌ 数据库验证失败")
        return False
    
    # 5. 导出数据库结构
    print("\n5. 导出数据库结构...")
    export_database_schema()
    
    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n📋 初始化信息:")
    print(f"• 数据库: {DB_CONFIG['database']}")
    print(f"• 主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("• 表结构: strategy_positions, internal_passwords")
    print("• 默认密码: admin123")
    print("• 示例策略: example_strategy")
    
    print("\n🚀 下一步:")
    print("1. 运行 Flask 应用: python src/app.py")
    print("2. 访问管理界面: http://localhost:5366")
    print("3. 使用API接口进行数据操作")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
