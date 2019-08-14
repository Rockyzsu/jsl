# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from collections import OrderedDict
from jsl.items import Relationship,JslItem
from jsl import config

class JslPipeline(object):
    def __init__(self):


        self.db = pymongo.MongoClient(host=config.mongo,port=config.port)

        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        self.collection = self.db['db_parker']['jsl']
        self.relations = self.db['db_parker']['jsl_relationship']

    def process_item(self, item, spider):

        if isinstance(item,JslItem):
            try:
                self.collection.update({'url':item['url']},OrderedDict(item),True,True)
            except Exception as e:
                print(e)

        elif isinstance(item,Relationship): # 这里会比较复杂
            # print(item)
            # user_id = scrapy.Field()
            # flag = scrapy.Field()
            # user = scrapy.Field()
            # prestige = scrapy.Field()  # 威望
            # approve = scrapy.Field()  # 赞同
            # follows_count = scrapy.Field()
            # fans_count = scrapy.Field()
            # follows_list = scrapy.Field()
            # fans_list = scrapy.Field()
            # crawltime = scrapy.Field()

            # 存在
            if list(self.relations.find({'user_id':item['user_id']})):
                if item['flag']=='follow': # 粉丝
                    follows_list = item['follows_list']
                    for follower in follows_list:
                        self.relations.update({'user_id':item['user_id']},{'$push':{'follows_list':follower}})
                else: # 关注他人
                    fans_list = item['fans_list']
                    for fan in fans_list:
                        self.relations.update({'user_id': item['user_id']}, {'$push': {'fans_list': fan}})

            # 不存在
            else:
                d=dict(item)
                del d['flag']
                self.relations.insert(d)


        return item

