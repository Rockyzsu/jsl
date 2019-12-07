# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime

import pymongo
from collections import OrderedDict

from scrapy.exporters import JsonLinesItemExporter
from jsl.items import Relationship, JslItem, UpdateItem
from jsl import config


class JslPipeline(object):
    def __init__(self):

        self.db = pymongo.MongoClient(host=config.mongodb_host, port=config.mongodb_port)
        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        # self.collection = self.db['db_parker']['jsl_20181108_allQuestion_test']
        self.collection = self.db['db_parker']['jsl']
        self.relations = self.db['db_parker']['jsl_relationship']
        try:
            self.collection.ensure_index('question_id', unique=True)
        except Exception as e:
            pass

    def process_item(self, item, spider):

        if isinstance(item, JslItem):
            update_time = datetime.datetime.now()
            item = dict(item)
            item['update_time'] = update_time
            if self.collection.find_one({'question_id': item['question_id']}):
                # 更新评论部分
                try:
                    self.collection.update_one({'question_id': item['question_id']},
                                               {'$set':
                                                    {'resp': item['resp'],
                                                     'last_resp_date': item['last_resp_date'],
                                                     'update_time': update_time
                                                     },

                                                }
                                               )
                except Exception as e:
                    print(e)
                else:
                    print(f'更新评论id: {item["question_id"]}')

            else:
                try:
                    self.collection.insert_one(OrderedDict(item))
                except Exception as e:
                    print(e)

        elif isinstance(item, Relationship):  # 这里会比较复杂

            # 存在
            if list(self.relations.find({'user_id': item['user_id']})):
                if item['flag'] == 'follow':  # 粉丝
                    follows_list = item['follows_list']
                    for follower in follows_list:
                        self.relations.update({'user_id': item['user_id']}, {'$push': {'follows_list': follower}})
                else:  # 关注他人
                    fans_list = item['fans_list']
                    for fan in fans_list:
                        self.relations.update({'user_id': item['user_id']}, {'$push': {'fans_list': fan}})

            # 不存在
            else:
                d = dict(item)
                del d['flag']
                self.relations.insert(d)

        return item


class ElasticPipeline(object):
    def __init__(self):
        self.fp = open('jsl.json', 'wb')
        self.exporter = JsonLinesItemExporter(self.fp, ensure_ascii=False, encoding='utf8')

    def open_spider(self, spider):
        print('开始爬虫了')

    def process_item(self, item, spider):
        print('处理item')
        self.exporter.export_item(item)

    def close_spider(self, spider):
        self.fp.close()
        print('爬虫结束')
