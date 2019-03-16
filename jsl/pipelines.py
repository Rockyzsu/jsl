# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from collections import OrderedDict
class JslPipeline(object):
    def __init__(self):
        self.db = pymongo.MongoClient(host='10.18.6.46',port=27001)
        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        self.collection = self.db['db_parker']['jsl']

    def process_item(self, item, spider):
        try:
            self.collection.update({'url':item['url']},OrderedDict(item),True,True)
        except Exception as e:
            print(e)


        return item
