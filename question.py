# -*-coding=utf-8-*-

# @Time : 2018/12/27 17:04
# @File : question.py

from scrapy import  cmdline

cmd = 'scrapy crawl questions -s LOG_FILE=log/question.log'
cmdline.execute(cmd.split())