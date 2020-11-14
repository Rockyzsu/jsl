# 每天的热帖

import datetime
import numpy as np
import pymongo
import pandas as pd
from settings import send_from_aliyun, llogger, _json_data
import re

last_time = -10  # 多少周之前

logger = llogger('log/trend_.log')
qq = _json_data['mongo']['qq']
host = qq['host']
port = qq['port']
user = qq['user']
password = qq['password']

connect_uri = f'mongodb://{user}:{password}@{host}:{port}'
db = pymongo.MongoClient(connect_uri)
MAX = 1000
current = datetime.datetime.now()

last_day = current + datetime.timedelta(hours=-32) # 脚本设置在早上8点运行
current_str = current.strftime("%Y-%m-%d")


def main():
    result = db['db_parker']['jsl'].find({},{'html':0}).sort('_id',pymongo.DESCENDING).limit(MAX)
    filter_result = []
    for i in result:
        createTime = i['createTime']
        createTime = datetime.datetime.strptime(createTime,'%Y-%m-%d %H:%M')
        if createTime >= last_day :
            title = i['title']
            creator = i['creator']
            resp_count = len(i['resp'])
            url = i['url']
            d = {'title':title,'url':url,'resp_count':resp_count}
            filter_result.append(d)

    hot_list = list(sorted(filter_result,key=lambda x:x['resp_count'],reverse=True))[:10]
    title,html = format_mail(hot_list)
    try:
        send_from_aliyun(title,html,types='html')

    except Exception as e:
        print(e)



def format_mail(hot_list):
    title='{} jsl TOP10'.format(current_str)
    content = ''
    for hl in hot_list:
        content+='<p><a font color="red" href="{}">{}</font> 回复：{}</p><p></p>'.format(hl['url'],hl['title'],hl['resp_count'])

    return title,content



if __name__ == '__main__':
    main()