# jsl
抓取集思录指定的用户的帖子，存档到mongo

#### 2020-11-27更新 加入登录JS加密与解密
[http://30daydo.com/article/44109](http://30daydo.com/article/44109)

<br>
使用方法：
安装scrapy + pymongo, 安装mongo服务器

安装完成后运行 python run.py
需要抓取指定的用户名：比如 毛之川
等待程序返回用户的id，然后把id 复制到spider/jisilu.py 文件中的 self.uid = '8132'， 替换这个值
修改pipeline.py文件中这一行
self.user = u'毛之川'  # 修改为指定的用户名 如 毛之川 

#### 新增爬取全站数据

#### guess_first_day_price_syncup.py 估算可转债上市价格

### 关注公众号: 可转债量化分析
![可转债量化分析](http://xximg.30daydo.com/picgo/kzz.jpg)