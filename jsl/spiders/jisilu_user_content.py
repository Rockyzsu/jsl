# -*- coding: utf-8 -*-
import datetime
import logging
import re
import scrapy
from jsl.question_parser import QuestionPageMixin
from jsl import config
from jsl.spiders.aes_encode import decoder
from scrapy import Request,FormRequest
# 获取某个用户的所有帖子，主要为了慎防大v要删帖，快速下载

class JisiluSpider(QuestionPageMixin, scrapy.Spider):
    only_add = False
    name = 'single_user'

    def __init__(self):
        super(JisiluSpider,self).__init__()

        self.headers = {
                        'Accept-Language': ' zh-CN,zh;q=0.9', 'Accept-Encoding': ' gzip, deflate, br',
                        'X-Requested-With': ' XMLHttpRequest', 'Host': ' www.jisilu.cn', 'Accept': ' */*',
                        'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36',
                        'Connection': ' keep-alive',
                        'Pragma': ' no-cache', 'Cache-Control': ' no-cache',
                        'Referer': ' https://www.jisilu.cn/people/dbwolf'
                        }

        # self.uid = '83220'  # 这个id需要在源码页面里面去找
        self.uid = config.uid

        self.list_url =  'https://www.jisilu.cn/people/ajax/user_actions/uid-{}__actions-101__page-{}'


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
            callback=self.start_fetch_user,
            dont_filter=True,

        )


    def start_fetch_user(self,response):
        current_page=0
        yield scrapy.Request(self.list_url.format(self.uid,current_page),headers=self.headers,meta={'current_page':current_page},callback=self.parse)

    def parse(self, response,**kwargs):
        current_page = response.meta['current_page']
        link_list = response.css('body > .aw-item')
        if not link_list:
            return

        for link in link_list:
            link_ = link.css('.aw-mod-head h4 a::attr(href)').get()
            match = re.search(r'/question/(\d+)', link_ or '')
            if match:
                question_id = match.group(1)
                yield scrapy.Request(self.DETAIL_URL.format(question_id),
                                     headers=self.headers,
                                     callback=self.check_detail,
                                     meta={'question_id':question_id})

        current_page=current_page+1
        yield scrapy.Request(self.list_url.format(self.uid,current_page),headers=self.headers,meta={'current_page':current_page},callback=self.parse)
