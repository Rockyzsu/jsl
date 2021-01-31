# 同步两个mongodb的数据

from settings import DBSelector
from loguru import logger
db=DBSelector()
remote=db.mongo('qq')['db_parker']['jsl']
local=db.mongo('local')['db_parker']['jsl']
remote_data = remote.find({},{'question_id':1,'resp_no':1})
for item in remote_data:
    question_id = item['question_id']
    find_doc = local.find_one({'question_id':question_id})
    if find_one:
    	pass
    else:
    	local.insert_one(find_one)
    	remote.delete_one({'_id':find_one['_id']})
    	logger.info(f'删除相同{question_id}')




