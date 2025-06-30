# 实时新闻的主题热度分析系统

##  项目简介

本项目为学校实训任务，旨在实现对新浪新闻滚动页面的实时新闻数据爬取、关键词分析与可视化展示。由于新浪新闻以财经类新闻为主，为丰富新闻类型，我们也爬取了部分观察者网新闻内容。

---

##  项目包含的技术

###  爬虫
- 多线程爬虫设计
- 阻塞式 `requests` 请求
- 数据解析使用 `BeautifulSoup` + 正则表达式提取
- 爬取平台：
  - 新浪新闻滚动页
  - 观察者网新闻页

###  可视化
- 后端框架：Flask
- 前端展示：Echarts、词云（WordCloud）

###  文本分析
- 分词与关键词提取：
  - `jieba`
  - `TextRank` 算法
- 相似度计算：
  - `TF-IDF` + 余弦相似度
  - 平均词向量 + 余弦相似度
- 词向量来源：[Chinese-Word-Vectors](https://github.com/Embedding/Chinese-Word-Vectors)

###  数据存储
- 使用 MySQL 数据库存储新闻标题、正文、时间、来源、浏览量、评论数等字段

---

##  搜索策略改进说明

起初我们在实现搜索功能时，使用了 `TF-IDF + 余弦相似度` 方法。但测试过程中发现部分实际相关性较高的新闻未能匹配成功。因此我们又引入了中文词向量表示（Word Embedding），使用 **平均词向量** 结合余弦相似度，提升了相关性匹配的准确度。

---

##  参考项目与资料

- 观察者网爬虫结构参考并修改自：
  [https://github.com/hunter-lee1/guanchazhe_spider](https://github.com/hunter-lee1/guanchazhe_spider?tab=readme-ov-file#%E8%A7%82%E5%AF%9F%E8%80%85%E6%96%B0%E9%97%BB%E7%BD%91%E7%88%AC%E8%99%AB%E6%96%B0%E9%97%BB%E7%88%AC%E8%99%AB)

- 中文词向量模型下载自：
  [https://github.com/Embedding/Chinese-Word-Vectors](https://github.com/Embedding/Chinese-Word-Vectors)

---

##  实现效果

