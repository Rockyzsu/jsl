# -*-coding=utf-8-*-

# @Time : 2020/1/1 0:08
# @File : trend.py
# 统计发帖趋势
import datetime
import numpy as np
import pymongo
import pandas as pd
from settings import send_from_aliyun,llogger,_json_data

last_time = -10 # 多少周之前

logger = llogger('log/trend_.log')
host = _json_data['mongo']['qq']['host']
# host='127.0.0.1'
port = _json_data['mongo']['qq']['port']
db = pymongo.MongoClient(host=host,port=port)
doc= db['db_parker']['jsl']
total_list = []
date = datetime.datetime.now() + datetime.timedelta(days=-365) # 一年内的数据

def main(send_mail=True):

    for item in doc.find({'last_resp_date':{'$gt':date}},{'html':0,'resp':0,'content':0}):
        del item['_id']
        total_list.append(item)

    df = pd.DataFrame(total_list)
    df['createTime']=pd.to_datetime(df['createTime'])
    df=df.set_index('createTime',drop=True)
    new_df = df.resample('W').count()
    show_data=new_df[['creator']].iloc[:last_time:-1]
    # print(show_data)
    # 最大值与
    max_index = new_df['creator'].idxmax().to_pydatetime().strftime('%Y-%m-%d')
    max_v=new_df['creator'].max()
    current = datetime.datetime.now().strftime('%Y-%m-%d')
    title=f'jsl一周发帖数量分析 {current}'
    percentage=np.round((show_data['creator'].values[:-1]-show_data['creator'].values[1:])/show_data['creator'].values[1:]*100,0)
    content = '|  日期  |  贴数  |  环比  |\n'
    # print(percentage)
    percentage=np.append(percentage,np.nan)
    start_index=0
    for index,item in show_data.iterrows():
        # print(index,item['creator'])
        py_date = index.to_pydatetime().strftime('%Y-%m-%d')
        count=item['creator']
        content+=f'| {py_date} | {count} | {percentage[start_index]}% |\n'
        start_index+=1
    content+=f'最大值发生在 {max_index}，贴数为 {max_v}\n'
    logger.info(title)
    logger.info(content)
    if send_mail:
        try:
            send_from_aliyun(title,content)
        except Exception as e:
            logger.error(e)


if __name__=='__main__':
    main(send_mail=True)
