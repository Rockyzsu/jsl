# jsl
抓取集思录指定的用户的帖子，存档到mongo

使用方法：
安装scrapy + pymongo, 安装mongo服务器

安装完成后运行 python run.py
需要抓取指定的用户名：比如 毛之川
等待程序返回用户的id，然后把id 复制到spider/jisilu.py 文件中的 self.uid = '8132'， 替换这个值
修改pipeline.py文件中这一行
self.user = u'毛之川'  # 修改为指定的用户名 如 毛之川 

#### 新增爬取全站数据
