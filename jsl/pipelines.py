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
        self.collection = self.db['jisilu'][u'flitter']
    def process_item(self, item, spider):
        self.collection.insert(OrderedDict(item))
        return item
