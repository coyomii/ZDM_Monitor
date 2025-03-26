# main.py
import logging
import random
import time

from config import config  # 从 config 文件夹导入 config 模块
from utils import database # 从 utils 文件夹导入 database 模块
from utils import scraper  # 从 utils 文件夹导入 scraper 模块
from utils import logger_setup # 从 utils 文件夹导入 logger_setup 模块


# --- 主逻辑 ---
def main():
    # !!! 调用新模块中的设置函数 !!!
    logger_setup.setup_logging()

    logging.info("--- SMZDM 价格监控启动 ---")
    database.init_db(config.DB_PATH)
    seen_deals_in_memory = database.load_seen_ids_from_db(config.DB_PATH)
    logging.info(f"监控商品列表: {config.SEARCH_TERMS}")

    try:
        while True:
            total_new_deals_this_run = 0
            for term in config.SEARCH_TERMS:
                logging.info(f"--- 开始检查 [{term}] ---")
                deals_for_term = []
                page = 1
                while True:
                    if page > config.SAFETY_BREAK_PAGE:
                        logging.warning(f"[{term}] 已检查超过 {config.SAFETY_BREAK_PAGE} 页，停止翻页。")
                        break

                    deals_on_page = scraper.fetch_deals(term, page)
                    if not deals_on_page:
                        logging.info(f"[{term}] 第 {page} 页未获取到符合条件的优惠，停止检查后续页码。")
                        break

                    deals_for_term.extend(deals_on_page)
                    page += 1
                    time.sleep(random.uniform(1, 3))

                new_deals_for_term_count = 0
                if not deals_for_term:
                    logging.info(f"[{term}] 本轮未获取到任何符合条件的优惠信息。")
                else:
                    logging.info(f"[{term}] 本轮共获取 {len(deals_for_term)} 条，开始处理...")
                    for deal in reversed(deals_for_term):
                        deal_id = deal['id']
                        if deal_id not in seen_deals_in_memory:
                            inserted = database.insert_deal(config.DB_PATH, deal, term)
                            if inserted:
                                new_deals_for_term_count += 1
                                # logging.info(f"✨ 新优惠 [{term}]! ✨ (时间: {deal.get('time_str', '?')})")
                                # logging.info(f"  标题: {deal['title']}")
                                # logging.info(f"  价格: {deal['price']}")
                                # logging.info(f"  点赞: {deal.get('likes', 'N/A')}, 评论: {deal.get('comments', 'N/A')}")
                                # logging.info(f"  平台: {deal.get('platform', 'N/A')}")
                                # logging.info(f"  链接: {deal['link']}")
                                # logging.info("-" * 20)
                                seen_deals_in_memory.add(deal_id)

                if new_deals_for_term_count > 0:
                    logging.info(f"[{term}] 本轮发现并入库 {new_deals_for_term_count} 条新优惠。")
                else:
                    logging.info(f"[{term}] 本轮未发现新优惠。")
                total_new_deals_this_run += new_deals_for_term_count
                logging.info(f"--- 完成检查 [{term}] ---\n")
                time.sleep(random.uniform(2, 5))

            logging.info(f"=== 本轮所有商品检查完成，共发现 {total_new_deals_this_run} 条新优惠 ===")

            wait_time = config.CHECK_INTERVAL_SECONDS + random.uniform(0, config.CHECK_INTERVAL_SECONDS * 0.1)
            logging.info(f"等待 {wait_time:.2f} 秒后进行下一轮检查...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        logging.info("用户手动停止监控。")
    except Exception as e:
        logging.error(f"主循环发生意外错误: {e}", exc_info=True)
    finally:
        logging.info("--- SMZDM 价格监控停止 ---")


if __name__ == "__main__":
    main()