# logger_setup.py
import logging
import logging.handlers
import os
import datetime
from config import config

def setup_logging():
    """配置日志记录，包括控制台和按天轮换的文件"""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    formatter = logging.Formatter(config.LOG_FORMAT)

    # 获取根 logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件 Handler (按天轮换)
    if not os.path.exists(config.LOG_FOLDER):
        try:
            os.makedirs(config.LOG_FOLDER)
        except OSError as e:
            # 注意：这里使用 print 而不是 logging.error，因为 logging 可能尚未完全配置好
            print(f"错误：创建日志目录 {config.LOG_FOLDER} 失败: {e}")
            return # 如果目录创建失败，可能无法继续文件日志记录

    today_str = datetime.date.today().strftime('%Y%m%d')
    log_filename = os.path.join(config.LOG_FOLDER, f"{today_str}.log")

    try:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filename,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # 使用 print 或 logging 记录成功信息
        print(f"日志系统设置完成，将输出到控制台和文件 '{log_filename}'。")

    except Exception as e:
         print(f"错误：设置文件日志处理器失败: {e}")