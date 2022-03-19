# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import logging

import pymongo
from collections import OrderedDict
from scrapy.exporters import JsonLinesItemExporter
from jsl.items import Relationship, JslItem
from jsl import config


class JslPipeline(object):

    def __init__(self):
        connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
        self.db = pymongo.MongoClient(connect_uri)
        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        # self.collection = self.db['db_parker']['jsl_20181108_allQuestion_test']
        self.collection = self.db['db_parker'][config.doc_name]
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


            if self.collection.find_one({'question_id': item['question_id']},{'_id':1}):
                # 更新评论部分, 不更新就退出
                only_add = False

                try:
                    only_add = item['only_add']

                except Exception as e:
                    pass

                if not only_add:
                    resp_no = self.collection.find_one({'question_id': item['question_id']},{'resp_no':1})
                    resp_no_num = resp_no.get('resp_no')

                    if resp_no_num<item['resp_no']:

                        print('最新的评论数多于数据库，更新')
                        try:
                            self.collection.update_one({'question_id': item['question_id']},
                                                       {'$set':
                                                            {'resp': item['resp'],
                                                             'resp_no':item['resp_no'],
                                                             'last_resp_date': item['last_resp_date'],
                                                             'update_time': update_time
                                                             },

                                                        }
                                                       )
                        except Exception as e:
                            logging.error(e)
                        else:
                            print('更新完毕')

                    else:
                        print('已有评论数目一样，跳过')


            else:
                # 直接新增
                try:
                    print('新增{}'.format(item['question_id']))
                    self.collection.insert_one(item)
                except Exception as e:
                    logging.error(e)

        elif isinstance(item, Relationship):  # 这里会比较复杂

            # 存在
            if list(self.relations.find({'user_id': item['user_id']},{'_id':1})):
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

