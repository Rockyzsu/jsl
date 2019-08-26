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
    resp_no = scrapy.Field()
