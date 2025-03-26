# database.py
import sqlite3
import logging
import datetime
import os
from config import config

def init_db(db_path):
    """初始化数据库，创建表结构，并确保目录存在"""
    db_folder = os.path.dirname(db_path)
    # 确保数据库目录存在
    if db_folder and not os.path.exists(db_folder):
        try:
            os.makedirs(db_folder)
            logging.info(f"创建数据库目录: {db_folder}")
        except OSError as e:
            logging.error(f"创建数据库目录 {db_folder} 失败: {e}")
            return # 如果目录创建失败，则不继续

    conn = None # 初始化 conn
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # !!! 修改表结构：增加 search_term 列，修改 first_seen 类型为 TEXT !!!
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                deal_id TEXT PRIMARY KEY,
                search_term TEXT NOT NULL,   -- 用于区分不同搜索词的商品
                title TEXT NOT NULL,
                price TEXT,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                platform TEXT,
                link TEXT UNIQUE NOT NULL,
                first_seen TEXT             -- 存储格式化的时间字符串
            )
        ''')
        # 可以考虑为 search_term 和 first_seen 添加索引以优化查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_term ON deals (search_term)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_first_seen ON deals (first_seen)")
        conn.commit()
        logging.info(f"数据库 '{db_path}' 初始化成功。")
    except sqlite3.Error as e:
        logging.error(f"数据库初始化失败: {e}")
    finally:
        if conn:
            conn.close()

def load_seen_ids_from_db(db_path):
    """从数据库加载所有已存在的 deal_id"""
    seen_ids = set()
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT deal_id FROM deals")
        rows = cursor.fetchall()
        seen_ids = {row[0] for row in rows}
        logging.info(f"从数据库加载了 {len(seen_ids)} 条已存在的优惠 ID。")
    except sqlite3.Error as e:
        logging.error(f"从数据库加载已见 ID 失败: {e}")
    finally:
        if conn:
            conn.close()
    return seen_ids

# !!! 修改 insert_deal: 增加 search_term 参数，手动插入 first_seen !!!
def insert_deal(db_path, deal_data, search_term):
    """将新的优惠信息插入数据库，如果 ID 或链接已存在则忽略"""
    inserted = False
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 获取当前本地时间并格式化
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT OR IGNORE INTO deals (
                deal_id, title, price, likes, comments, platform, link, search_term, first_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            deal_data['id'],
            deal_data['title'],
            deal_data['price'],
            deal_data.get('likes', 0),
            deal_data.get('comments', 0),
            deal_data.get('platform', '未知'),
            deal_data['link'],
            search_term, # 插入搜索词
            current_time_str # 插入当前时间字符串
        ))
        conn.commit()
        if cursor.rowcount > 0:
            inserted = True
            logging.debug(f"成功插入新优惠到数据库: ID {deal_data['id']} (搜索词: {search_term})")
    except sqlite3.Error as e:
        logging.error(f"插入数据库失败: {e}, 数据: {deal_data}, 搜索词: {search_term}")
    except KeyError as e:
        logging.error(f"插入数据库时缺少关键数据: {e}, 数据: {deal_data}")
    finally:
        if conn:
            conn.close()
    return inserted