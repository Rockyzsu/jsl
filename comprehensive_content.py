from scrapy import  cmdline
import datetime
# 获取指定日期内的所有帖子

# cmd = 'scrapy crawl allcontent'
cmd = 'scrapy crawl allcontent -s LOG_FILE=log/allcontent-{}.log -a daily=no'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
cmdline.execute(cmd.split())