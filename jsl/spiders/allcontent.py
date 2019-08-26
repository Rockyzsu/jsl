# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging


class AllcontentSpider(scrapy.Spider):
    name = 'allcontent'

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
        url = 'https://www.jisilu.cn/account/ajax/login_process/'
        data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': config.username,
            'password': config.password,
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

    def parse(self, response):
        total_page = 5

        for i in range(1, total_page + 1):
            focus_url = 'https://www.jisilu.cn/home/explore/sort_type-new__category-__day-0__is_recommend-__page-{}'.format(
                i)
            yield Request(url=focus_url, headers=self.headers, callback=self.parse_page, dont_filter=True)

    def parse_page(self, response):
        nodes = response.xpath('//div[@class="aw-question-list"]/div')
        for node in nodes:
            each_url = node.xpath('.//h4/a/@href').extract_first()
            yield Request(url=each_url, headers=self.headers, callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        item = JslItem()
        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()
        s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()
        ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)

        try:
            content = ret[0].strip()
        except:
            content = None

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/span/text()').extract_first()

        resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

        url = response.url

        # 添加发起人
        try:
            item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
        except Exception as e:
            print(e)
            item['creator'] = None

        item['title'] = title.strip()
        item['content'] = content
        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            logging.warning(e)
            logging.warning('没有回复')
            item['resp_no'] = None

        item['createTime'] = createTime
        item['url'] = url.strip()
        yield item
