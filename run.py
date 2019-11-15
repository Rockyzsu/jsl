# -*-coding=utf-8-*-

__author__ = 'Rocky'
'''
http://30daydo.com
Email: weigesysu@qq.com
'''
from scrapy import  cmdline
import requests
import re

def search_id():
    name = input(u'请输入你需要抓取的用户名: ')
    url = 'https://www.jisilu.cn/people/{}'.format(str(name))
    # url ='https://www.jisilu.cn/people/持有封基'
    r = requests.get(url)
    user_id = re.findall('var PEOPLE_USER_ID = \'(\d+)\';'  , r.text)
    print(user_id[0])

def main():
    # search_id()
    # exit()

    cmd = 'scrapy crawl allcontent'



if __name__ == '__main__':
    main()