import requests
import random
import re
import time
import pymysql
from bs4 import BeautifulSoup
from lxml import etree
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # 替换为你的数据库用户名
    'password': '123456',  # 替换为你的数据库密码
    'database': 'newdb',
    'charset': 'utf8mb4'
}

# 用户代理列表和随机请求头函数保持不变
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
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Origin': 'https://www.guancha.cn',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
def save_to_database(data_list):
    """保存数据到sina_news表（完全匹配表结构）"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 构建与表结构完全匹配的INSERT语句
        insert_sql = """
        INSERT INTO sina_news (
            网址, 标题, 内容, 发布时间, 来源, 浏览量, 评论数
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        ) ON DUPLICATE KEY UPDATE 
            标题=VALUES(标题),
            内容=VALUES(内容),
            发布时间=VALUES(发布时间),
            来源=VALUES(来源),
            浏览量=VALUES(浏览量),
            评论数=VALUES(评论数)
        """
        
        for data in data_list:
            # 处理数据转换
            title = data['标题'].replace('_', ' ') if isinstance(data['标题'], str) else data['标题']
            content = data['内容']
            publish_time = data['发布时间']
            source = data['来源']
            
            # 处理数字字段
            try:
                view_count = int(data['浏览量']) if str(data['浏览量']).isdigit() else 0
            except:
                view_count = 0
                
            try:
                comment_count = int(data['评论数']) if str(data['评论数']).isdigit() else 0
            except:
                comment_count = 0
            
            # 执行插入
            cursor.execute(insert_sql, (
                data['网址'],  # 注意这里使用中文列名"网址"
                title,
                content,
                publish_time,
                source,
                view_count,
                comment_count
            ))
        
        conn.commit()
        print(f"成功保存 {len(data_list)} 条记录到sina_news表")
    except Exception as e:
        print(f"保存到数据库时出错: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def request_with_retry(url, retries=3):
    for attempt in range(retries):
        headers = get_random_headers()
        try:
            resp = requests.get(url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == retries - 1:  # 只在最后一次尝试失败时打印
                print(f"请求失败 {url}")
            time.sleep(3)
    return None

def extract_docid(html, url):
    patterns = [
        r'var\s+_DOC_ID\s*=\s*["\'](\d+)["\']',
        r'id=["\'](\d+)["\']',
        r'"docId"\s*:\s*["\'](\d+)["\']',
        r'/(\d+)_\d+\.shtml'  
    ]
    url_match = re.search(r'/(\d+)_\d+\.shtml', url)
    if url_match:
        return url_match.group(1)
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None

def get_view_count(docid):
    if not docid:
        return "0"
    count_url = f"https://user.guancha.cn/news-api/view-count?postId={docid}"
    headers = {
        **get_random_headers(),
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.guancha.cn',
        'Accept': 'application/json'
    }
    try:
        time.sleep(random.uniform(1.0, 1.2))
        resp = requests.get(count_url, headers=headers, timeout=10, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            view_count = data.get("view_count_text")
            return view_count if view_count else "0"  
    except Exception:
        return "0"

def get_comment_count(docid):
    if not docid:
        return "0"
    comment_url = f"https://user.guancha.cn/comment/hot-comment-list-after-article?codeId={docid}&codeType=1"
    headers = {
        **get_random_headers(),
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://www.guancha.cn/article/{docid}.shtml',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive'
    }
    try:
        time.sleep(random.uniform(1.0, 1.5))
        resp = requests.get(comment_url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            all_count = extract_all_count(resp.text)
            return str(all_count) if all_count is not None else "0"
        elif resp.status_code == 403:
            return "blocked"
    except Exception:
        return "0"

def extract_all_count(json_text):
    patterns = [
        r'"all_count"\s*:\s*(\d+)',
        r'"total"\s*:\s*(\d+)',
        r'commentCount["\']?\s*:\s*["\']?(\d+)'
    ]
    for pattern in patterns:
        m = re.search(pattern, json_text)
        if m:
            return int(m.group(1))
    return None

def parse_article(url):
    response = request_with_retry(url)
    if not response:
        return None
    
    html = response.text
    docid = extract_docid(html, url)
    
    view_count = get_view_count(docid)
    comment_count = get_comment_count(docid)

    soup = BeautifulSoup(html, 'html.parser')
    item = {'网址': url}

    title_tag = soup.select_one('div.article-content > h1') or soup.find('h3') or soup.select_one('div.article-content > div > h1')
    item['标题'] = title_tag.get_text(strip=True) if title_tag else '无标题'

    time_tag = soup.select_one('span.time1') or soup.select_one('div.time span')
    item['发布时间'] = time_tag.get_text(strip=True) if time_tag else ''

    content_ps = soup.select('div.article-txt-content p') or soup.select('div.content p')
    raw_content = ''.join(p.get_text(strip=True) for p in content_ps)

    cleaned_content = re.sub(r'扫一扫\s*下载观察者APP\s*', '', raw_content, flags=re.IGNORECASE)
    item['内容'] = re.sub(r'\s+', '', cleaned_content)

    item.update({
        '浏览量': view_count,
        '评论数': comment_count,
        '来源': '观察者网'
    })

    return item

def get_article_urls():
    urls = []
    for page in range(1,3):
        list_url = f'https://www.guancha.cn/mainnews-yw/list_{page}.shtml'
        print(f"获取列表页: {list_url}")
        response = request_with_retry(list_url)
        if not response:
            continue
        
        html = etree.HTML(response.text)
        links = html.xpath("//div[@class='right fn']/h4/a/@href")
        full_links = ['https://www.guancha.cn' + link for link in links]
        urls.extend(full_links)
        time.sleep(1)
    return urls

def worker(url):
    data = parse_article(url)
    if data:
        print(f"已获取: {data['标题']}")
    return data

def main():
    article_urls = get_article_urls()
    print(f"共发现{len(article_urls)}篇文章")

    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, url) for url in article_urls]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception:
                pass
    
    # 所有任务完成后保存到数据库
    if results:
        save_to_database(results)
        print(f"数据已保存到sina_news表，共 {len(results)} 条记录")

if __name__ == '__main__':
    main()