# config.py
import os

# --- 监控配置 ---
SEARCH_TERMS = ["充电宝", "固态硬盘"] # 同时监控 SSD 和显卡
CHECK_INTERVAL_SECONDS = 60 * 10 # 检查间隔

# --- 数据库配置 ---
DB_FOLDER = "database" # 数据库存放的文件夹名
DB_FILENAME = "smzdm_deals.db" # 数据库文件名
DB_PATH = os.path.join(DB_FOLDER, DB_FILENAME) # 数据库完整路径

# --- 抓取配置 ---
BASE_URL = "https://search.smzdm.com/"
SAFETY_BREAK_PAGE = 50 # 最大页数
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Referer': 'https://www.smzdm.com/'
}

# --- 日志配置 ---
LOG_FOLDER = "logs"
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s' # 可以加入 %(name)s 显示模块名
# LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s' # 可以加入 %(name)s 显示模块名