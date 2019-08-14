# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2019/5/12 20:11
# @File : relationship.py
import datetime
import re

import math
# from scrapy.linkextractors import LinkExtractor

from scrapy import Spider, Request
from jsl.items import Relationship


class RelationshipSpider(Spider):
    name = 'relation'
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

    people_url = 'https://www.jisilu.cn/people/{name}'
    follow_url = 'https://www.jisilu.cn/people/ajax/follows/type-follows__uid-{user_id}__page-{page}' # 关注的人
    fan_url = 'https://www.jisilu.cn/people/ajax/follows/type-fans__uid-{user_id}__page-{page}' # 粉丝

    def start_requests(self):
        start_user = '帅牛'

        yield Request(
            url=self.people_url.format(name=start_user),
            headers=self.headers,
            meta={'user': start_user},
            callback=self.parse_user
        )

    def parse_user(self, response):

        item = Relationship()

        user = response.meta['user']

        follows_num = int(
            response.xpath('//div[@class="pull-left aw-user-center-follow-mini-mod"][1]/b/em/text()').extract_first())
        fans_num = int(
            response.xpath('//div[@class="pull-left aw-user-center-follow-mini-mod"][2]/b/em/text()').extract_first())

        prestige = int(response.xpath('//i[@class="aw-icon i-user-prestige"]/following::*[1]/text()').extract_first())
        approve = int(response.xpath('//i[@class="aw-icon i-user-approve"]/following::*[1]/text()').extract_first())

        user_id = re.search('var PEOPLE_USER_ID = \'(\d+)\';', response.text)

        if user_id:
            user_id = user_id.group(1)

        item['user'] = user
        item['user_id'] = user_id
        item['follows_count'] = follows_num
        item['fans_count'] = fans_num

        item['approve'] = approve
        item['prestige'] = prestige

        follows_pages = int(math.ceil(follows_num / 30))
        fans_pages = int(math.ceil(fans_num / 30))
        for follow_page in range(follows_pages):
            yield Request(
                url=self.follow_url.format(user_id=user_id, page=follow_page),
                headers=self.headers,
                callback=self.follow_item,
                meta={'item': item.copy()}
            )

        for fan_page in range(fans_pages):
            yield Request(
                url=self.fan_url.format(user_id=user_id, page=fan_page),
                headers=self.headers,
                callback=self.fan_item,
                meta={'item': item.copy()}
            )

    def follow_item(self, response):
        item = response.meta['item']
        item['flag'] = 'follow'

        follow_list = []
        for node in response.xpath('//li[@class="span5"]'):
            d = {}
            follower_name = node.xpath('.//div[@class="aw-item"]/p[1]/a/text()').extract_first()
            prestige = int(node.xpath('.//i[@class="aw-icon i-user-prestige"]/following::*[1]/text()').extract_first())
            approve = int(node.xpath('.//i[@class="aw-icon i-user-approve"]/following::*[1]/text()').extract_first())
            d['follow_name'] = follower_name
            d['prestige'] = prestige
            d['approve'] = approve
            follow_list.append(d)

            yield Request(
                url=self.people_url.format(name=follower_name),
                headers=self.headers,
                meta={'user': follower_name},
                callback=self.parse_user
            )

        item['follows_list'] = follow_list
        item['crawltime'] = datetime.datetime.now()
        yield item

    def fan_item(self, response):

        item = response.meta['item']
        item['flag'] = 'fan'

        follow_list = []
        for node in response.xpath('//li[@class="span5"]'):
            d = {}
            fan_name = node.xpath('.//div[@class="aw-item"]/p[1]/a/text()').extract_first()
            prestige = int(node.xpath('.//i[@class="aw-icon i-user-prestige"]/following::*[1]/text()').extract_first())
            approve = int(node.xpath('.//i[@class="aw-icon i-user-approve"]/following::* [1]/text()').extract_first())

            d['fan_name'] = fan_name
            d['prestige'] = prestige
            d['approve'] = approve
            yield Request(
                url=self.people_url.format(name=fan_name),
                headers=self.headers,
                meta={'user': fan_name},
                callback=self.parse_user
            )

            follow_list.append(d)

        item['fans_list'] = follow_list
        item['crawltime'] = datetime.datetime.now()
        yield item
