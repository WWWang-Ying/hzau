import pymysql
import jieba.analyse
import numpy as np
from datetime import datetime
from wordcloud import WordCloud
import io
import base64
from pypinyin import lazy_pinyin, Style
from collections import defaultdict
from datetime import datetime
from collections import Counter

import numpy as np


# 加载词向量
word_vectors = {}
vector_dim = 0
print(f"正在加载词向量库: baidubaike_word_vectorslbq.txt")

with open("baidubaike_word_vectorslbq.txt", 'r', encoding='utf-8') as f:
    first_line = f.readline().split()
    if len(first_line) >= 2:
        try:
            total_words = int(first_line[0])
            vector_dim = int(first_line[1])
            print(f"词向量库信息: 总词数={total_words}, 维度={vector_dim}")
        except ValueError:
            print("警告: 无法解析第一行的基本信息")
            vector_dim = len(first_line) - 1
            print(f"假设向量维度为: {vector_dim}")
    else:
        print("警告: 第一行格式不正确")
        vector_dim = 300
        print(f"假设向量维度为: {vector_dim}")

    for line in f:
        parts = line.strip().split()
        if len(parts) < 10:
            continue
        try:
            word = parts[0]
            vec = np.array([float(x) for x in parts[1:vector_dim+1]])
            word_vectors[word] = vec
        except ValueError:
            try:
                first_num_index = next(
                    i for i, x in enumerate(parts[1:], 1)
                    if x.replace('.', '', 1).isdigit() or
                       (x[0] == '-' and x[1:].replace('.', '', 1).isdigit())
                )
                word = "".join(parts[:first_num_index])
                vec = np.array([float(x) for x in parts[first_num_index:first_num_index+vector_dim]])
                word_vectors[word] = vec
            except:
                continue

print(f"成功加载 {len(word_vectors)} 个词向量")

# 批量计算余弦相似度函数
def cosine_similarity_batch(query_vec, doc_matrix):
    dot_products = np.dot(doc_matrix, query_vec.T).flatten()  # (N,)
    doc_norms = np.linalg.norm(doc_matrix, axis=1)
    query_norm = np.linalg.norm(query_vec)
    denom = doc_norms * query_norm
    denom[denom == 0] = 1e-10  # 防止除零
    return dot_products / denom

# 连接数据库并提取数据库内容
def get_datalist():
    datalist = []
    cnn = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8')
    cursor = cnn.cursor()
    sql = ' select * from sina_news '
    cursor.execute(sql)
    for item in cursor.fetchall():
        datalist.append(item)
    cursor.close()
    cnn.close()
    return datalist

# 计算平均词向量函数
def average_word_vector(words):
    vectors = []
    for w in words:
        if w in word_vectors:
            vectors.append(word_vectors[w])
        elif len(w) > 1:
            sub_vectors = []
            for c in w:
                if c in word_vectors:
                    sub_vectors.append(word_vectors[c])
            if sub_vectors:
                vectors.append(np.mean(sub_vectors, axis=0))
    if not vectors:
        return np.zeros(vector_dim)
    return np.mean(vectors, axis=0)

def parse_publish_time(time_str):
    try:
        # 示例：'2024年06月12日 10:25'
        return datetime.strptime(time_str.strip(), "%Y年%m月%d日 %H:%M")
    except Exception as e:
        print(f"时间解析失败: {time_str}, 错误: {e}")
        return datetime.min  # 排在最后

def get_anwers(query_text, sort_by="default"):
    datalist = []
    cnn = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8')
    cursor = cnn.cursor()
    cursor.execute("SELECT * FROM sina_news")
    for item in cursor.fetchall():
        datalist.append(item)

    doc_vectors = []
    for row in datalist:
        keyword_str = row[8]
        if keyword_str:
            keywords = [kw.strip() for kw in keyword_str.replace('，', ',').split(',') if kw.strip()]
            vec = average_word_vector(keywords)
            doc_vectors.append(vec)
        else:
            doc_vectors.append(np.zeros(vector_dim))

    
    # 使用 jieba TextRank 提取关键词，若为空则用jieba分词代替
    try:
        query_keywords = jieba.analyse.textrank(
            query_text, topK=5, withWeight=False,
            allowPOS=('ns', 'n', 'vn', 'v', 'nr', 'a')  # 扩展词性，减少空结果
        )
        query_keywords = [kw.strip() for kw in query_keywords if kw.strip()]
        if len(query_keywords) == 0:
            print("TextRank提取关键词为空，使用jieba分词结果作为关键词")
            query_keywords = list(set(jieba.cut(query_text)))
    except Exception as e:
        print(f"提取查询关键词时出错: {str(e)}")
        query_keywords = []
    print("\n查询关键词 (最终使用):", query_keywords)
    # 计算查询的平均词向量
    query_vec = average_word_vector(query_keywords) if query_keywords else np.zeros(vector_dim)

    # 转换为矩阵形式
    doc_matrix = np.vstack(doc_vectors)  # (N, vector_dim)
    query_vec = query_vec.reshape(1, -1)  # (1, vector_dim)

    # 计算相似度
    doc_sims = cosine_similarity_batch(query_vec, doc_matrix)

    # 组合索引与相似度
    doc_similarities = list(enumerate(doc_sims))

    # 排序输出
    sorted_results = sorted(doc_similarities, key=lambda x: x[1], reverse=True)
    # 返回相似度最高的前30条datalist
    top30_results = [datalist[idx] for idx, sim in sorted_results[:30]]
    word_freq = {}
    for doc in top30_results:
        keywords = doc[8].split(',')  # 用逗号拆分关键词
        for kw in keywords:
            kw = kw.strip()
            if kw not in word_freq:
                word_freq[kw] = 0
            word_freq[kw] += 1  # 统计关键词的出现次数

    # === 排序逻辑 ===
    if sort_by == "time":
        # 按发布时间排序（倒序）
        sorted_news = sorted(top30_results, key=lambda x: parse_publish_time(x[4]), reverse=True)
    elif sort_by == "views":
        # 按浏览量排序（倒序）
        sorted_news = sorted(top30_results, key=lambda x: int(x[6]), reverse=True)
    elif sort_by == "comments":
        # 按评论数排序（倒序）
        sorted_news = sorted(top30_results, key=lambda x: int(x[7]), reverse=True)
    else:
        # 默认按相似度排序
        sorted_news = top30_results

    # 取前100词（根据出现次数排序）
    top_n = 100
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

    wordcloud_data = [{"name": k, "value": v} for k, v in top_words]

    return wordcloud_data, sorted_news






def get_hot_anwers(start_date, end_date):
    # 将传入的时间字符串转换为 datetime 对象
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

    # 获取数据
    cnn1 = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb', charset='utf8')
    cursor1 = cnn1.cursor()
    datalist = get_datalist()  # 假设 get_datalist() 是获取所有新闻数据的函数
    
    # 根据日期过滤新闻
    filtered_news = choose(datalist, start_date, end_date)
    cursor1.close()
    cnn1.close()
    return filtered_news




def parse_chinese_datetime(text):
    try:
        return datetime.strptime(text, "%Y年%m月%d日 %H:%M")
    except Exception as e:
        return None  # 如果格式不对则跳过该项

def choose(datalist, start_date, end_date):
    print(f"start_date: {start_date}, end_date: {end_date}")
    filtered = []
    for item in datalist:
        publish_time_str = item[4]
        publish_time = parse_chinese_datetime(publish_time_str)
        if not publish_time:
            continue
        print(f"publish_time: {publish_time}")
        if start_date and publish_time < start_date:
            print(f"Skip: {publish_time} < {start_date}")
            continue
        if end_date and publish_time > end_date:
            print(f"Skip: {publish_time} > {end_date}")
            continue
        filtered.append(item)
    print(f"Filtered count: {len(filtered)}")
    return filtered


def get_keyword_data(start_date, end_date):
    # 将传入的时间字符串转换为 datetime 对象
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

    # 获取数据
    cnn1 = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb', charset='utf8')
    cursor1 = cnn1.cursor()
    datalist = get_datalist()  # 假设 get_datalist() 是获取所有新闻数据的函数
    
    # 根据日期过滤新闻
    filtered_news = choose(datalist, start_date, end_date)

    # 提取关键词，并进行词频统计
    keywords = []
    for item in filtered_news:
        keyword_str = item[8]  # 假设第 8 个字段是关键词字段，关键词之间以逗号分隔
        keywords.extend(keyword_str.split(','))  # 分割并添加到关键词列表中

    # 统计每个关键词的出现频率
    keyword_count = Counter(keywords)
    
     # 按频率降序排序并解包为 words, weights
    words, weights = zip(*keyword_count.most_common(20)) if keyword_count else ([], [])
    # 关闭数据库连接
    cursor1.close()
    cnn1.close()
    return list(words), list(weights)






def wordcloud_png(start_date, end_date):
    # 将传入的时间字符串转换为 datetime 对象
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

    # 获取数据
    cnn1 = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb', charset='utf8')
    cursor1 = cnn1.cursor()
    datalist = get_datalist()  # 假设 get_datalist() 是获取所有新闻数据的函数
    
    # 根据日期过滤新闻
    filtered_news = choose(datalist, start_date, end_date)

    # 提取关键词，并进行词频统计
    keywords = []
    for item in filtered_news:
        keyword_str = item[8]  # 假设第 8 个字段是关键词字段，关键词之间以逗号分隔
        keywords.extend(keyword_str.split(','))  # 分割并添加到关键词列表中

    # 统计每个关键词的出现频率
    keyword_count = Counter(keywords)
    
    # 选择前 300 个最频繁的关键词
    word_freq = dict(keyword_count.most_common(300))

    # 创建词云
    x, y = np.ogrid[:800, :800]
    tree_mask = (x - 400) ** 2 + (y - 400) ** 2 > 300 ** 2
    tree_mask = 255 * tree_mask.astype(int)

    wc = WordCloud(
        font_path='simhei.ttf',  # 使用黑体
        background_color='white',
        mask=tree_mask,
        max_words=200,
        contour_width=3,
        contour_color='green',
        colormap='summer'  # 夏季配色
    ).generate_from_frequencies(word_freq)

    # 将词云图保存为 PNG 图片并转为 base64 编码
    img = io.BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')

    # 关闭数据库连接
    cursor1.close()
    cnn1.close()

    return img_base64, len(filtered_news), len(word_freq)


def get_num():
    cnn1 = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8')
    cursor1 = cnn1.cursor()
    sql1 = "SELECT keyword, total_tf FROM tfidf_vocab ORDER BY total_tf DESC "
    cursor1.execute(sql1)
    result = cursor1.fetchall()
    word_freq = {row[0]: row[1] for row in result}
    # 关键词数
    keyword_count = len(word_freq)
    cursor1.close()
    cnn1.close()

    cnn2 = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8')
    cursor2 = cnn2.cursor()
    sql2 = "SELECT COUNT(*) FROM sina_news" 
    cursor2.execute(sql2)
    # 查询新闻总数
    news_count = cursor2.fetchone()[0]
    cursor2.close()
    cnn2.close()

    return news_count, keyword_count




def get_verbs():
    cnn = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    cursor = cnn.cursor()
    sql = "SELECT id, keyword, total_tf FROM tfidf_vocab "
    cursor.execute(sql)
    result = cursor.fetchall()
    id = [row['id'] for row in result]
    words = [row['keyword'] for row in result]
    weights = [row['total_tf'] for row in result]
    cursor.close()
    cnn.close()
    return id, words, weights

def get_words_grouped_by_initial():
    id, words, weights = get_verbs()

    def get_initial(word):
        initials = lazy_pinyin(word, style=Style.FIRST_LETTER)
        return initials[0].upper() if initials else "#"

    # 构造分组结构
    grouped = defaultdict(list)
    for id, w, wt in zip(id, words, weights):
        initial = get_initial(w)
        grouped[initial].append({"id":id, "word": w, "weight": wt})

    # 排序：每组内词按字典序，外部按字母顺序
    grouped_sorted = dict(sorted(
        ((k, sorted(v, key=lambda x: x["word"])) for k, v in grouped.items()),
        key=lambda item: item[0]
    ))

    return grouped_sorted



def source_summary():
    cnn = pymysql.connect(
        host='localhost',
        user='root',
        password='20051004',
        port=3306,
        database='newdb',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = cnn.cursor()
    sql = "SELECT 来源, 出现次数 FROM source_counts"
    cursor.execute(sql)
    result = cursor.fetchall()

    words = []
    weights = []
    other_count = 0

    for row in result:
        if row['出现次数'] < 200:
            other_count += row['出现次数']
        else:
            words.append(row['来源'])
            weights.append(row['出现次数'])

    if other_count > 0:
        words.append('其他')
        weights.append(other_count)

    cursor.close()
    cnn.close()
    return words, weights


def get_top50_sources():
    cnn = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8',cursorclass=pymysql.cursors.DictCursor)
    cursor = cnn.cursor()
    sql = "SELECT 来源, 出现次数, 平均评论数, 平均浏览量 FROM source_counts  WHERE 来源 <> '观察者网' ORDER BY 出现次数 DESC LIMIT 50;"
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    cnn.close()
    return result


def get_word_detail_by_id(id, page=1, per_page=10):
    
    
    cnn = pymysql.connect(host='localhost', user='root', password='20051004', port=3306, database='newdb',
                          charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    cursor = cnn.cursor()

    # 查询关键词基本信息
    cursor.execute("SELECT keyword, total_tf FROM tfidf_vocab WHERE id = %s", (id,))
    keyword_info = cursor.fetchone()

    if not keyword_info:
        cnn.close()
        return None

    # 查询该关键词对应文章总数，用于分页
    cursor.execute("SELECT COUNT(*) AS total_count FROM keyword_article WHERE keyword_id = %s", (id,))
    total_count = cursor.fetchone()['total_count']

    # 计算分页起始位置
    offset = (page - 1) * per_page

    # 查询关键词对应文章列表，分页查询
    cursor.execute("""
        SELECT article_id, url, title
        FROM keyword_article
        WHERE keyword_id = %s
        ORDER BY CAST(article_id AS UNSIGNED) ASC
        LIMIT %s OFFSET %s
    """, (id, per_page, offset))
    articles = cursor.fetchall()

    cnn.close()

    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page

    return {
        'id': id,  # 加入 id
        'keyword': keyword_info['keyword'],
        'total_tf': keyword_info['total_tf'],
        'articles': articles,
        'total_count': total_count,
        'pages': total_pages,     # 注意这里用pages，不用total_pages
        'current_page': page,     # current_page 和模板detail.page保持对应
        'page': page,             # 模板中可能有用到detail.page，建议保留
        'per_page': per_page
    }

