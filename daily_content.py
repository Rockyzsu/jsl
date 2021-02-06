# -*-coding=utf-8-*-

# @Time : 2018/12/27 16:58
# @File : daily_content.py
from scrapy import  cmdline
import datetime
# 获取指定日期内的所有帖子

cmd = 'scrapy crawl allcontent -s LOG_FILE=log/allcontent-{}.log -a daily=yes'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
cmdline.execute(cmd.split())
