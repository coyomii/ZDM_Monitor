# scraper.py
import requests
from bs4 import BeautifulSoup
import logging
import datetime
from urllib.parse import quote
from config import config

def parse_count(tag):
    """尝试从标签文本中解析数字，失败返回0"""
    if tag:
        text = tag.text.strip()
        count_str = ''.join(filter(str.isdigit, text))
        if count_str.isdigit():
            return int(count_str)
    return 0

def fetch_deals(search_term, page_num=1):
    """从什么值得买搜索结果页获取并解析优惠信息 (指定搜索词和页码)"""
    deals = []
    encoded_search_term = quote(search_term)
    search_url = f"{config.BASE_URL}?c=home&s={encoded_search_term}&v=b&mx_v=b&p={page_num}"
    logging.info(f"抓取 [{search_term}] 第 {page_num} 页")

    try:
        response = requests.get(search_url, headers=config.HEADERS, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            logging.warning(f"[{search_term}] 第 {page_num} 页非 HTML 内容: {content_type}。")
            return []

        soup = BeautifulSoup(response.text, 'lxml')
        deal_list_container = soup.find('ul', id='feed-main-list')

        if not deal_list_container:
            logging.info(f"[{search_term}] 第 {page_num} 页未找到列表容器。")
            return []

        list_items = deal_list_container.find_all('li', class_=lambda x: x and 'feed-row-wide' in x.split())

        if not list_items:
             logging.info(f"[{search_term}] 第 {page_num} 页未找到商品项。")
             return []

        today_str_md = datetime.date.today().strftime('%m-%d')
        deals_found_on_page = 0 # 记录本页找到符合条件的数量

        for item in list_items:
            # --- 筛选 ---
            is_domestic_deal = item.find('span', class_='search-guonei-mark')
            if not is_domestic_deal:
                continue

            time_container = item.find('span', class_='feed-block-extras')
            is_today = False
            time_text_for_log = "未知时间"
            platform = "未知"
            if time_container:
                time_text = time_container.text.strip()
                time_text_for_log = time_text
                platform_spans = time_container.find_all('span')
                if platform_spans:
                    # 平台名可能是最后一个span，也可能是倒数第二个（如果最后是扫码购）
                    # 简单起见，我们先取最后一个，如果它是'扫码购'，则尝试取倒数第二个
                    last_span_text = platform_spans[-1].text.strip()
                    if last_span_text == '扫码购' and len(platform_spans) > 1:
                         platform = platform_spans[-2].text.strip()
                    elif last_span_text: # 确保不是空字符串
                         platform = last_span_text
                    # else: platform 保持 "未知"

                # 判断是否当天 (逻辑不变)
                if '刚刚' in time_text or '分钟前' in time_text or '小时前' in time_text:
                    is_today = True
                else:
                    parts = time_text.split()
                    if parts:
                        time_str_part = parts[0]
                        if ':' in time_str_part and '-' not in time_str_part:
                            is_today = True
                        elif '-' in time_str_part:
                            date_part = time_str_part.split()[0]
                            if date_part == today_str_md:
                                is_today = True
            else:
                 logging.debug(f"[{search_term}] 未找到时间容器，跳过项。")
                 continue

            if not is_today:
                # logging.debug(f"[{search_term}] 跳过非当天项: {time_text_for_log}")
                continue # 如果不是今天，处理下一个 item

            # --- 提取信息 (逻辑不变，加入了点赞/评论/平台) ---
            title_tag_container = item.find('h5')
            title_tag = title_tag_container.find('a') if title_tag_container else None

            if title_tag:
                title = title_tag.text.strip()
                link = title_tag.get('href')
                if link and not link.startswith('http'):
                    link = 'https:' + link

                price = "N/A"
                price_tag = item.find('span', class_='z-highlight')
                if not price_tag:
                     price_tag = item.find('div', class_='z-highlight')
                if price_tag:
                    price = price_tag.text.strip()

                like_tag = item.find('span', class_='price-btn-up')
                like_count_tag = like_tag.find_all('span')[1] if like_tag and len(like_tag.find_all('span')) > 1 else None
                like_count = parse_count(like_count_tag)

                comment_tag = item.find('a', class_='feed-btn-comment')
                comment_count = parse_count(comment_tag)

                deal_id = item.get('data-aid') or item.get('articleid')
                if not deal_id and link:
                    try:
                        path_parts = [part for part in link.split('/') if part]
                        if path_parts:
                            potential_id = path_parts[-1].split('?')[0].split('#')[0]
                            deal_id = f"link_{potential_id}"
                        else:
                           deal_id = link
                    except Exception as e_id:
                         logging.warning(f"[{search_term}] 提取ID出错: {e_id} Link: {link}")
                         deal_id = link

                if deal_id and link:
                    deals_found_on_page += 1
                    deals.append({
                        'id': str(deal_id),
                        'title': title,
                        'price': price,
                        'likes': like_count,
                        'comments': comment_count,
                        'platform': platform,
                        'link': link,
                        'time_str': time_text_for_log
                    })
                else:
                    logging.warning(f"[{search_term}] 无法确定ID或缺少链接: {title}")

        logging.info(f"[{search_term}] 第 {page_num} 页找到 {deals_found_on_page} 条符合条件的优惠。")

    except requests.exceptions.RequestException as e:
        logging.error(f"[{search_term}] HTTP 请求失败 (第 {page_num} 页): {e}")
    except Exception as e:
        logging.error(f"[{search_term}] 解析错误 (第 {page_num} 页): {e}", exc_info=True)
        # 可选：保存错误页面
        # try: ... except ...

    return deals