# 同步两个mongodb的数据
import pymongo
from settings import DBSelector
from loguru import logger

logger.add('syncup.log')
db=DBSelector()
client = db.mongo('qq')
remote=client['db_parker']['jsl']
local=pymongo.MongoClient()['db_parker']['jsl']
remote_data = remote.find()

# 更新本地数据
def update(item,question_id,update=False):
    del item['_id']

    if update:
        local.update_one({'question_id':question_id},{'$set':{'resp':item['resp'],'resp_no':item['resp_no']}})
    else:
        local.insert_one(item)
    remote.delete_one({'question_id': question_id})

def remove(item):
    remote.delete_one({'_id': item['_id']})



for item in remote_data:
    question_id = item['question_id']
    local_find_doc = local.find_one({'question_id':question_id})
    if local_find_doc:
        resp_no = item['resp_no']

        if resp_no<=local_find_doc['resp_no']:
            try:
                remove(item)
            except Exception as e:
                logger.error(e)
            else:
                logger.info(f'删除相同{question_id}')

        else:
            try:
                update(item,question_id,True)
            except Exception as e:
                logger.error(e)

            else:
                logger.info(f'更新本地{question_id}')
    else:
        try:
            update(item,question_id,False)
        except Exception as e:
            logger.error(e)
        else:
           logger.info(f'删除不存在,备份后的{question_id}')
