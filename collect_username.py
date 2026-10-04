# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2020/9/5 14:25
# @File : collect_username.py
import pymongo
from settings import _json_data
import codecs
from loguru import logger

host = _json_data['mongo']['qq']['host']
port = _json_data['mongo']['qq']['port']
user = _json_data['mongo']['qq']['port']
connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
client = pymongo.MongoClient(connect_uri)

doc = client['db_parker']['jsl']

def collect_creator():
    creators = doc.find({},{'creator':1})
    user_set = set()
    count = 0
    for create in creators.batch_size(100):
        print(count)
        count+=1
        name = create.get('creator')
        # print(name)
        if name is not None and isinstance(name,str):
            user_set.add(name)
    user_list = list(user_set)
    user_str = '\n'.join(user_list)
    with codecs.open('creator.txt','w',encoding='utf8') as f:
        f.write(user_str)


def get_user(filename):
    user_list = None
    with codecs.open(filename,'r',encoding='utf8') as f:
        user_list = f.readlines()
        user_list=set(map(lambda x:x.strip(),user_list))
    return user_list

def repler():
    resps = doc.find({},{'resp':1,'_id':0})
    user_set = set()
    count = 0
    creartor_set = get_user('creator.txt')

    for  resp in resps.batch_size(500):
        resp_list = resp.get('resp')
        if resp_list:
            for resp_ in resp_list:
                name=list(resp_.keys())[0]
                if name not in creartor_set and name not in user_set:
                    count += 1
                    print(count)
                    print(name)
                    user_set.add(name)
    user_list = list(user_set)
    user_str = '\n'.join(user_list)
    with codecs.open('reply.txt','w',encoding='utf8') as f:
        f.write(user_str)

repler()
logger.info('Done')


