#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日重置任务脚本
用于每天0点重置用户策略请求次数
可以通过crontab或任务计划程序调用
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import SQLALCHEMY_DATABASE_URI
from src.models.models import db, UserStrategy, init_redis
from src.app import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_reset.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def reset_daily_request_counts():
    """重置每日请求次数"""
    try:
        app = create_app()
        
        with app.app_context():
            # 方法1：使用SQLAlchemy ORM
            today = datetime.now().date()
            
            # 找到昨天有请求记录的用户策略
            strategies_to_reset = UserStrategy.query.filter(
                UserStrategy.last_request_date < today,
                UserStrategy.daily_request_count > 0,
                UserStrategy.is_active == True
            ).all()
            
            reset_count = 0
            for strategy in strategies_to_reset:
                strategy.daily_request_count = 0
                reset_count += 1
            
            db.session.commit()
            
            logger.info(f"成功重置 {reset_count} 条用户策略的每日请求次数")
            
            # 方法2：使用原生SQL（可选，更高效）
            # engine = create_engine(SQLALCHEMY_DATABASE_URI)
            # with engine.connect() as connection:
            #     result = connection.execute(text("""
            #         UPDATE user_strategies 
            #         SET daily_request_count = 0 
            #         WHERE last_request_date < CURDATE() 
            #         AND daily_request_count > 0 
            #         AND is_active = 1
            #     """))
            #     connection.commit()
            #     logger.info(f"使用SQL重置了 {result.rowcount} 条记录")
            
            return True
            
    except Exception as e:
        logger.error(f"重置每日请求次数失败: {e}")
        return False

def cleanup_old_records():
    """清理历史记录（可选）"""
    try:
        app = create_app()
        
        with app.app_context():
            # 清理30天前的非活跃策略记录
            cutoff_date = datetime.now().date() - timedelta(days=30)
            
            old_records = UserStrategy.query.filter(
                UserStrategy.last_request_date < cutoff_date,
                UserStrategy.is_active == False
            ).count()
            
            if old_records > 0:
                UserStrategy.query.filter(
                    UserStrategy.last_request_date < cutoff_date,
                    UserStrategy.is_active == False
                ).delete()
                
                db.session.commit()
                logger.info(f"清理了 {old_records} 条30天前的非活跃策略记录")
            
            return True
            
    except Exception as e:
        logger.error(f"清理历史记录失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始执行每日重置任务...")
    
    success = True
    
    # 重置每日请求次数
    if not reset_daily_request_counts():
        success = False
    
    # 清理历史记录（可选）
    # if not cleanup_old_records():
    #     success = False
    
    if success:
        logger.info("每日重置任务执行成功")
        return 0
    else:
        logger.error("每日重置任务执行失败")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
