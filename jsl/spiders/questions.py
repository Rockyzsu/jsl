# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.question_parser import QuestionPageMixin
from jsl import config
import logging
import pymongo

# 遍历所有questions id 看从哪里开始
class QuestionSpider(QuestionPageMixin, scrapy.Spider):
    legacy_replies = True
    name = 'questions'

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

    POST_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-add_time__category-__day-0__is_recommend-__page-{}'  # 发帖日期
    RESP_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-new__category-__day-0__is_recommend-__page-{}'  # 回帖按照日期

    # self.doc =
    connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
    db = pymongo.MongoClient(connect_uri)
    # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
    # self.collection = self.db['db_parker']['jsl_20181108_allQuestion_test']
    collection = db['db_parker'][config.doc_name]

    def start_requests(self):
        login_url = 'https://www.jisilu.cn/login/'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,br', 'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
            'Host': 'www.jisilu.cn', 'Pragma': 'no-cache', 'Referer': 'https://www.jisilu.cn/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36'}

        yield Request(url=login_url, headers=headers, callback=self.login, dont_filter=True)

    def login(self, response):
        url = 'https://www.jisilu.cn/webapi/account/login_process/'
        data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': config.jsl_user,
            'password': config.jsl_password,
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }

        yield FormRequest(
            url=url,
            headers=self.headers,
            formdata=data,
            callback=self.parse,
        )

    def question_exist(self,_id):
        return True if self.collection.find_one({'question_id':_id},{'_id':1}) else False

    def parse(self, response,**kwargs):
        lastest_id = config.LASTEST_ID  #

        for i in range(lastest_id + 5000, 1, -1):
            if not self.question_exist(lastest_id):
                focus_url = 'https://www.jisilu.cn/question/{}'.format(i)
                yield Request(url=focus_url, headers=self.headers, callback=self.parse_item, meta={'question_id': str(i)})
    def parse_item(self, response):
        yield from self.check_detail(response)
