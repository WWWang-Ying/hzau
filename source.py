import pymysql

# 数据库连接配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '20051004',
    'database': 'newdb',
    'charset': 'utf8mb4'
}

# 连接数据库
connection = pymysql.connect(**config)

try:
    with connection.cursor() as cursor:
        # 1. 创建 source_counts 表（如果不存在）
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS source_counts (
            来源 VARCHAR(255),
            出现次数 INT,
            平均评论数 FLOAT,
            平均浏览量 FLOAT
        );
        """
        cursor.execute(create_table_sql)

        # 2. 清空表内容
        cursor.execute("TRUNCATE TABLE source_counts;")

        # 3. 统计并插入数据
        insert_sql = """
        INSERT INTO source_counts (来源, 出现次数, 平均评论数, 平均浏览量)
        SELECT 
            来源,
            COUNT(*) AS 出现次数,
            AVG(评论数) AS 平均评论数,
            AVG(浏览量) AS 平均浏览量
        FROM sina_news
        GROUP BY 来源;
        """
        cursor.execute(insert_sql)

    # 提交事务
    connection.commit()
    print("表创建与数据插入完成。")

except Exception as e:
    print("执行出错:", e)
    connection.rollback()

finally:
    connection.close()
