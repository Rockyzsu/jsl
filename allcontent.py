# -*-coding=utf-8-*-

# @Time : 2018/12/27 16:58
# @File : allcontent.py
from scrapy import  cmdline
import datetime
cmd = 'scrapy crawl allcontent -s LOG_FILE=log/allcontent-{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
cmdline.execute(cmd.split())
