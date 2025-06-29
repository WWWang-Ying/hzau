import pymysql
import pandas as pd
import jieba.analyse

# MySQL 配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '20051004',
    'database': 'newdb'
}

def connect_db():
    return pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset='utf8mb4'
    )

def fetch_data_from_db():
    conn = connect_db()
    query = "SELECT id, 网址, 标题, 内容 FROM sina_news WHERE 内容 IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def extract_keywords(df):
    df['keyword'] = df['内容'].astype(str).apply(
        lambda x: ', '.join(jieba.analyse.textrank(x, topK=5, withWeight=False))
    )
    return df

def save_keywords_to_keyword_article(df):
    conn = connect_db()
    cursor = conn.cursor()

    # 创建 keyword_article 表（如果表不存在的话）
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS keyword_article (
        keyword_id INT NOT NULL,
        article_id VARCHAR(50),
        url VARCHAR(255),
        title VARCHAR(255)
    )
    '''
    try:
        cursor.execute(create_table_query)
        print("表 'keyword_article' 已创建或已存在。")
    except pymysql.MySQLError as e:
        print(f"创建表时出错: {e}")
        conn.rollback()
        return

    # 获取 tfidf_vocab 中所有的关键词及对应的 keyword_id
    cursor.execute("SELECT id, keyword FROM tfidf_vocab")
    keyword_map = {row[1]: row[0] for row in cursor.fetchall()}

    # 清空旧数据
    cursor.execute("DELETE FROM keyword_article")

    keyword_article_records = []
    
    # 遍历每篇文章
    for index, row in df.iterrows():
        article_id = row['id']
        url = row['网址']
        title = row['标题']
        
        # 获取该文章的关键词
        keywords = row['keyword'].split(', ')
        
        for keyword in keywords:
            keyword_id = keyword_map.get(keyword)
            if keyword_id is not None:
                keyword_article_records.append((keyword_id, article_id, url, title))

    # 按照 keyword_id 排序记录
    keyword_article_records = sorted(keyword_article_records, key=lambda x: x[0])

    # 批量插入数据到 keyword_article 表
    for record in keyword_article_records:
        cursor.execute(
            'INSERT INTO keyword_article (keyword_id, article_id, url, title) VALUES (%s, %s, %s, %s)',
            record
        )

    conn.commit()
    conn.close()
    print("词汇与文章信息已保存到 keyword_article 表中。")

def main():
    df = fetch_data_from_db()  # 获取数据
    df = extract_keywords(df)  # 提取关键词
    save_keywords_to_keyword_article(df)  # 保存数据到 keyword_article 表

if __name__ == "__main__":
    main()
