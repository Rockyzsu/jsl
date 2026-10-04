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


            existing = self.collection.find_one(
                {'question_id': item['question_id']}, {'resp': 1, 'resp_no': 1})
            if existing is not None:
                if item.get('only_add', False):
                    return item

                replies = item.get('resp')
                count = item.get('resp_no')
                if not isinstance(replies, list) or not replies:
                    logging.warning('帖子 %s 的回复为空，跳过更新', item['question_id'])
                    return item
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    logging.warning('帖子 %s 的回复数为空或无效，跳过更新', item['question_id'])
                    return item

                stored_replies = existing.get('resp')
                stored_length = len(stored_replies) if isinstance(stored_replies, list) else 0
                stored_count = existing.get('resp_no')
                if not isinstance(stored_count, int) or isinstance(stored_count, bool):
                    stored_count = stored_length

                # 同时检查实际抓取条数和页面声明总数，防止漏页结果覆盖完整数据。
                if len(replies) < stored_length or count < stored_count:
                    logging.warning(
                        '帖子 %s 的回复数减少，跳过更新（实际 %s/%s，总数 %s/%s）',
                        item['question_id'], len(replies), stored_length, count, stored_count)
                    return item

                try:
                    self.collection.update_one(
                        {'question_id': item['question_id']},
                        {'$set': {'resp': replies,
                                  'resp_no': count,
                                  'last_resp_date': item.get('last_resp_date'),
                                  'update_time': update_time}})
                except Exception as e:
                    logging.error(e)

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

