-- JQ-QMT 数据库结构
-- 生成时间: 2025-07-19 20:54:14

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `quant` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `quant`;


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
    


    CREATE TABLE IF NOT EXISTS `internal_passwords` (
        `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `password_hash` varchar(64) NOT NULL COMMENT '密码哈希值',
        `created_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        `updated_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内部密码表';
    


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
    

-- 默认数据
INSERT IGNORE INTO `internal_passwords` (`password_hash`, `created_time`, `updated_time`) VALUES
(SHA2('admin123', 256), NOW(), NOW());

-- 创建默认管理员用户（密码: admin123）
INSERT IGNORE INTO `users` (`username`, `password_hash`, `is_superuser`, `is_active`, `created_time`, `updated_time`) VALUES
('admin', SHA2('admin123', 256), 1, 1, NOW(), NOW());
