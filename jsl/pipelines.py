# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from collections import OrderedDict
class JslPipeline(object):
    def __init__(self):
        self.db = pymongo.MongoClient('raspberrypi')
        self.user = u'持有封基' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        self.collection = self.db['jisilu'][self.user]
    def process_item(self, item, spider):
        self.collection.insert(OrderedDict(item))
        return item
