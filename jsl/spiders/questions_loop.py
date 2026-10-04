# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.question_parser import QuestionPageMixin
from jsl import config
import logging

LASTEST_ID = config.LASTEST_ID  # 394716


# 遍历所有questions id 看从哪里开始
class AllcontentSpider(QuestionPageMixin, scrapy.Spider):
    legacy_replies = True
    name = 'questions_loop'

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
            callback=self.parse_,
        )

    def parse_(self, response):
        print(response.text)
        start_page = LASTEST_ID

        focus_url = 'https://www.jisilu.cn/question/{}'.format(start_page)
        yield Request(url=focus_url, headers=self.headers, callback=self.parse_item, meta={'question_id': start_page, 'dont_redirect': True,},
                      dont_filter=True)

    def parse_item(self, response):
        question_id = response.meta['question_id'] - 1
        if question_id > 1:
            yield Request(url=self.DETAIL_URL.format(question_id), headers=self.headers,
                          callback=self.parse_item,
                          meta={'question_id': question_id, 'dont_redirect': True},
                          dont_filter=True)
        if '问题不存在或已被删除' not in response.text:
            yield from self.check_detail(response)
