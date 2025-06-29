import pymysql
import jieba
import jieba.analyse
import numpy as np
from collections import defaultdict
import pandas as pd

# MySQL 配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '20051004',
    'database': 'newdb'
}

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

# 连接到数据库
def connect_db():
    conn = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    return conn

# 创建 tfidf_vocab 表
def create_tfidf_vocab_table():
    conn = connect_db()
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS tfidf_vocab (
        id INT AUTO_INCREMENT PRIMARY KEY,   -- 自动递增的主键
        keyword VARCHAR(255) NOT NULL,        -- 关键词
        total_tf INT NOT NULL                -- 关键词总出现次数
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print("tfidf_vocab 表已创建或已存在。")

# 从数据库中读取数据
def fetch_data_from_db():
    conn = connect_db()
    query = "SELECT id, 网址, 标题, 内容 FROM sina_news WHERE 内容 IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

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

# 提取关键词并记录关键词及其出现次数
def extract_and_count_keywords(df):
    keyword_count = defaultdict(int)
    
    # 提取每条内容的关键词
    for content in df['内容']:
        if pd.notna(content):
            keywords = jieba.analyse.textrank(content, topK=5, withWeight=False)
            for keyword in keywords:
                keyword_count[keyword] += 1

    return keyword_count

# 保存关键词及其出现次数到数据库，并按频率降序排序
def save_keywords_to_db(keyword_count):
    conn = connect_db()
    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("DELETE FROM tfidf_vocab")
    cursor.execute("ALTER TABLE tfidf_vocab AUTO_INCREMENT = 1")

    # 将关键词按照出现次数降序排序
    sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)

    # 插入排序后的关键词和频率数据
    for keyword, count in sorted_keywords:
        cursor.execute('INSERT INTO tfidf_vocab (keyword, total_tf) VALUES (%s, %s)', (keyword, count))

    conn.commit()
    conn.close()
    print("关键词和频率已保存到 tfidf_vocab 表中，并按频率排序。")

# 更新文档的关键词和平均词向量到 sina_news 表
def update_keywords_and_vectors_in_db(df):
    conn = connect_db()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        # 提取关键词
        keywords = jieba.analyse.textrank(row['内容'], topK=5, withWeight=False)
        keywords_str = ','.join(keywords)
        
        # 计算文档的平均词向量
        avg_vector = average_word_vector(keywords)
        avg_vector_str = ','.join(map(str, avg_vector))  # 将向量转换为字符串
        
        # 更新文档的关键词和平均词向量
        cursor.execute(""" 
            UPDATE sina_news 
            SET keyword = %s, average_vector = %s 
            WHERE id = %s
        """, (keywords_str, avg_vector_str, row['id']))

    conn.commit()
    conn.close()
    print("文档的关键词和平均词向量已保存到 sina_news 表中。")

# 主程序
def main():
    # 创建 tfidf_vocab 表
    create_tfidf_vocab_table()
    
    # 获取数据
    df = fetch_data_from_db()
    
    # 提取并统计关键词出现次数
    keyword_count = extract_and_count_keywords(df)
    
    # 保存关键词到数据库
    save_keywords_to_db(keyword_count)

    # 更新文档的关键词和平均词向量到 sina_news 表
    update_keywords_and_vectors_in_db(df)

if __name__ == "__main__":
    main()
