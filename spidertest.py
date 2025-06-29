import requests
import json
from bs4 import BeautifulSoup
import re
import pymysql
from lxml import etree
import threading
from queue import Queue
import traceback
import random

USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/53"
]

def get_random_headers():
    return {'User-Agent': random.choice(USER_AGENTS)}

lock = threading.Lock()
data_queue = Queue()
page_counter = 1

def main():
    baseurl = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num=50&page="
    threads = []
    for i in range(10):
        t = threading.Thread(target=thread_task, args=(baseurl,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    datalist = []
    while not data_queue.empty():
        datalist.append(data_queue.get())
    saveData(datalist)

def thread_task(baseurl):
    global page_counter
    while True:
        with lock:
            if page_counter > 2000:
                break
            current_page = page_counter
            page_counter += 1

        url = baseurl + str(current_page)
        try:
            data = getURL(url)
            if data:
                for item in data:
                    data_queue.put(item)
        except Exception as e:
            print(f"[线程异常] 页面：{url}，错误：{e}")
            traceback.print_exc()

def getURL(url):
    headers = get_random_headers()
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data_json = json.loads(response.content)
        news = data_json.get("result", {}).get("data", [])
    except Exception as e:
        print(f"[getURL异常] URL：{url}，错误：{e}")
        traceback.print_exc()
        return None

    results = []
    for new in news:
        detail = askURL(new.get("url"))
        if detail:
            results.append(detail)
            print(f"成功：{detail['标题']}")
        else:
            print(f"失败：{new.get('url')}")
    return results

def askURL(url):
    detail = {"网址": url}
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
    except Exception as e:
        print(f"[askURL请求失败] URL：{url}，错误：{e}")
        traceback.print_exc()
        return None

    try:
        title = soup.find(class_="main-title")
        detail["标题"] = title.text.strip() if title else ""

        artibody = soup.find(class_="article")
        if artibody:
            text = re.sub(r'\s+', ' ', artibody.text).strip()
            text = re.sub(r'海量资讯、精准解读，尽在新浪财经APP.*$', '', text)
            detail["内容"] = text
        else:
            detail["内容"] = ""

        date_source = soup.find(class_="date-source")
        if date_source:
            spans = date_source.find_all("span")
            detail["发布时间"] = spans[0].text.strip() if spans else ""
            detail["来源"] = date_source.a.text.strip() if date_source.a else (spans[1].text.strip() if len(spans) > 1 else "")
        else:
            detail["发布时间"] = ""
            detail["来源"] = ""

        total, show = getCommentCounts(url)
        detail["评论数"] = show
        detail["浏览量"] = total
    except Exception as e:
        print(f"[askURL解析失败] URL：{url}，错误：{e}")
        traceback.print_exc()
        return None

    return detail

def getCommentCounts(url):
    commentURLPattern = "https://comment5.news.sina.com.cn/page/info?version=1&format=js&channel={}&newsid={}&group=&compress=0&ie=utf-8&oe=utf-8&page=1&page_size=20"
    try:
        page_content = requests.get(url, timeout=5).content
    except Exception as e:
        print(f"[获取评论页面失败] {url}，错误：{e}")
        traceback.print_exc()
        return 0, 0

    try:
        root = etree.HTML(page_content)
        comment_meta = root.xpath('//meta[contains(@content, "comment_channel")]/@content')
        if not comment_meta:
            return 0, 0

        comment_channel, comment_id = None, None
        comment_info = comment_meta[0].split(";")
        for c in comment_info:
            if "comment_channel" in c:
                comment_channel = c.split(":")[-1]
            elif "comment_id" in c:
                comment_id = c.split(":")[-1]

        if not comment_channel or not comment_id:
            return 0, 0

        commenturl = commentURLPattern.format(comment_channel, comment_id)
        comments = requests.get(commenturl, timeout=5)
        comments.encoding = 'utf-8'
        jd = json.loads(comments.text.strip('var data='))
        return jd['result']['count']['total'], jd['result']['count']['show']

    except Exception as e:
        print(f"[评论解析失败] URL：{url}，错误：{e}")
        traceback.print_exc()
        return 0, 0

def saveData(data):
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='20051004',
            database='newdb'
        )
        cursor = conn.cursor()

        # 获取已有网址避免重复插入
        cursor.execute("SELECT 网址 FROM sina_news")
        existing_urls = set(row[0] for row in cursor.fetchall())

        insert_count = 0
        for row in data:
            if row['网址'] in existing_urls:
                continue
            cursor.execute('''
                INSERT INTO sina_news (网址, 标题, 内容, 发布时间, 来源, 评论数, 浏览量)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                row['网址'], row['标题'], row['内容'], row['发布时间'],
                row['来源'], row['评论数'], row['浏览量']
            ))
            insert_count += 1

        conn.commit()
        print(f"✅ 成功保存 {insert_count} 条新数据")

    except Exception as e:
        print(f"[数据库写入失败] 错误：{e}")
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
