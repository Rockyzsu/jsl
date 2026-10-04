# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.question_parser import QuestionPageMixin
from jsl import config
import logging
from jsl.spiders.aes_encode import decoder
import pymongo

# 按照日期爬取, 会损失新人贴

class WeekContentSpider(QuestionPageMixin, scrapy.Spider):
    only_add = False
    name = 'week_content'

    headers = {
        'Host': 'www.jisilu.cn', 'Connection': 'keep-alive', 'Pragma': 'no-cache',
        'Cache-Control': 'no-cache', 'Accept': 'application/json,text/javascript,*/*;q=0.01',
        'Origin': 'https://www.jisilu.cn', 'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Referer': 'https://www.jisilu.cn/login/',
        'Accept-Encoding': 'gzip,deflate,br',
        'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8'
    }

    start_page = 1

    POST_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-add_time__category-__day-0__is_recommend-__page-{}'  # 发帖日期
    RESP_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-new__category-__day-0__is_recommend-__page-{}'  # 回帖按照日期

    def __init__(self, daily='yes', *args, **kwargs):
        super().__init__(*args, **kwargs)

        if daily == 'yes':

            self.logger.info('按照周')
            self.DAYS = 14  # 获取2周的帖子
            self.URL = self.POST_DATE_URL

        self.last_week = datetime.datetime.now() + datetime.timedelta(days=-1 * self.DAYS)


        connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
        self.db = pymongo.MongoClient(connect_uri)
        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        self.collection = self.db['db_parker'][config.doc_name]

    def start_requests(self):

        login_url = 'https://www.jisilu.cn/login/'
        headersx = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,br', 'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
            'Host': 'www.jisilu.cn', 'Pragma': 'no-cache', 'Referer': 'https://www.jisilu.cn/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36'}

        yield Request(url=login_url, headers=headersx, callback=self.login, dont_filter=True)

    def login(self, response):
        url = 'https://www.jisilu.cn/webapi/account/login_process/'
        username = decoder(config.jsl_user)
        jsl_password = decoder(config.jsl_password)
        data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': username,
            'password': jsl_password,
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }

        yield FormRequest(
            url=url,
            headers=self.headers,
            formdata=data,
            callback=self.parse,
            dont_filter=True
        )

    def parse(self, response, **kwargs):
        print('登录后', response.text)
        focus_url = self.URL.format(self.start_page)

        yield Request(url=focus_url, headers=self.headers, callback=self.parse_page, dont_filter=True,
                      meta={'page': self.start_page})

    def question_exist(self, _id):
        return bool(self.collection.find_one({'question_id': _id}, {'_id': 1}))
