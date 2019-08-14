# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JslItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    creator = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    createTime = scrapy.Field()
    resp = scrapy.Field()
    resp_no = scrapy.Field()
    crawlTime = scrapy.Field()
    last_resp_date = scrapy.Field()

class Relationship(scrapy.Item):
    user_id =scrapy.Field()
    flag=scrapy.Field()
    user=scrapy.Field()
    prestige=scrapy.Field() # 威望
    approve=scrapy.Field() # 赞同
    follows_count=scrapy.Field()
    fans_count=scrapy.Field()
    follows_list=scrapy.Field()
    fans_list=scrapy.Field()
    crawltime=scrapy.Field()