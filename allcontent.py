# -*-coding=utf-8-*-

# @Time : 2018/12/27 16:58
# @File : allcontent.py
from scrapy import  cmdline

cmd = 'scrapy crawl allcontent -s LOG_FILE=allcontent.log'
cmdline.execute(cmd.split())
