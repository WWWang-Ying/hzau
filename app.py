from flask import Flask, render_template, request
from datetime import datetime
import useful_functions
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

datalist = useful_functions.get_datalist()

app = Flask(__name__)
app.config["SECRET_KEY"] = "12345678"


from datetime import datetime

def filter_news_by_date(news_data, start_date=None, end_date=None):
    """
    过滤新闻数据，根据开始日期和结束日期进行筛选
    :param news_data: 新闻数据
    :param start_date: 开始日期 (datetime对象)
    :param end_date: 结束日期 (datetime对象)
    :return: 过滤后的新闻数据
    """
    filtered_news = []
    
    for new in news_data:
        # new[4]是新闻的发布时间（格式为：xxxx年xx月xx日 xx:xx）
        news_date_str = new[4]
        try:
            # 更新日期时间格式，处理包含时间的字符串
            news_date = datetime.strptime(news_date_str, "%Y年%m月%d日 %H:%M")  # 包含小时和分钟
        except ValueError:
            # 如果格式不对，输出错误日志（也可以根据需要进行处理）
            print(f"日期格式错误: {news_date_str}")
            continue
        
        # 根据时间范围筛选
        if start_date and news_date < start_date:
            continue
        if end_date and news_date > end_date:
            continue
        
        filtered_news.append(new)

    return filtered_news

@app.route('/')
def index():
    form = SearchForm()
    return render_template("index.html", form=form)

@app.route('/search.html')
def search():
    return render_template('search.html')

@app.route('/news.html', methods=['GET'])
def news_page():
    page = request.args.get('page', 1, type=int)  # 获取当前页，默认1
    per_page = 50  # 每页50条新闻
    total = len(datalist)  # 新闻总数
    pages = (total + per_page - 1) // per_page  # 总页数，向上取整

    # 获取开始日期和结束日期
    start_date_str = request.args.get("startDate")
    end_date_str = request.args.get("endDate")
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M") if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M") if end_date_str else None

    # 根据日期过滤新闻
    filtered_news = useful_functions.choose(datalist, start_date, end_date)

    # 分页处理
    total = len(filtered_news)  # 过滤后的新闻数量
    pages = (total + per_page - 1) // per_page  # 总页数，向上取整
    start = (page - 1) * per_page
    end = start + per_page
    news_page = filtered_news[start:end]  # 当前页新闻切片

    return render_template("news.html", news=news_page, page=page, pages=pages)

@app.route('/word.html')
def word_page():
    # 获取传递过来的时间参数
    start_date = request.args.get('start-date')
    end_date = request.args.get('end-date')

    # 调用函数并传递时间参数
    img_base64, news_count, keyword_count = useful_functions.wordcloud_png(start_date, end_date)

    # 返回模板并传递参数
    return render_template("word.html", img_base64=img_base64, news_count=news_count, keyword_count=keyword_count,start_date=start_date,end_date=end_date)

@app.route('/analysis.html')
def analysis_page():
    # 获取传递过来的时间参数
    start_date = request.args.get('start-date')
    end_date = request.args.get('end-date')

    words, weights = useful_functions.get_keyword_data(start_date, end_date)
    return render_template("analysis.html",words = words, weights =weights,start_date=start_date,end_date=end_date)

class SearchForm(FlaskForm):
    search_creater = StringField('creater', validators=[DataRequired()])
    submit = SubmitField('搜索')




@app.route('/news_result.html', methods=['GET'])
def newsResult_page():
    form = SearchForm()
    search = request.args.get("query", "")
    sort_by = request.args.get("sort_by", "default")

    # 调用带排序方式的搜索函数
    wordcloud_data, search_list = useful_functions.get_anwers(search, sort_by)

    titles = [item[2] for item in search_list]
    pub_times = [item[4] for item in search_list]
    views = [item[6] for item in search_list]
    comments = [item[7] for item in search_list]

    return render_template("news_result.html",
                           form=form,
                           wordcloud_data=wordcloud_data,
                           news=search_list,
                           titles=titles,
                           pub_times=pub_times,
                           views=views,
                           comments=comments,
                           sort_by=sort_by)



@app.route('/hot_result.html', methods=['GET', 'POST'])
def hot_hot_newsResult_page():
    # 获取传递过来的时间参数
    start_date = request.args.get('start-date')
    end_date = request.args.get('end-date')

    datalist = useful_functions.get_hot_anwers(start_date, end_date)
    datalist_sorted = sorted(datalist, key=lambda x: x[4])

    titles = [item[2] for item in datalist_sorted]  # 假设 item[0] 是标题
    pub_times = [item[4] for item in datalist_sorted]
    views = [item[6] for item in datalist_sorted]
    comments = [item[7] for item in datalist_sorted]

    return render_template ("hot_result.html",
                           news=datalist_sorted,
                           titles=titles,
                           pub_times=pub_times,
                           views=views,
                           comments=comments,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/num.html')
def keywords():
    word_data = useful_functions.get_words_grouped_by_initial()
    return render_template('num.html', word_data=word_data)

@app.route('/word_doc.html')
def word_doc():
    id = request.args.get('id')  # 关键词
    page = int(request.args.get('page', 1))  # 当前页码，默认为 1
    per_page = 10  # 每页显示的文章数量

    detail = useful_functions.get_word_detail_by_id(id, page=page, per_page=per_page)

    if detail is None:
        # 关键词不存在，返回一个提示页面或者404
        return "关键词不存在或无数据", 404

    return render_template('word_doc.html', detail=detail)


@app.route('/index')
@app.route('/index.html')
def get_index():
    news_count, keyword_count = useful_functions.get_num()
    return render_template("index.html", news_count=news_count, keyword_count=keyword_count)


@app.route('/source.html')
def get_source():
    words, weights = useful_functions.source_summary()
    return render_template("source.html",words = words, weights =weights)

@app.route('/quality.html')
def quality_result():
    result = useful_functions.get_top50_sources()
    return render_template('quality.html',data = result)

@app.route('/choose.html')
def choose():
    return render_template('choose.html')

if __name__ == '__main__':
    app.run()
