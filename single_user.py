from scrapy import  cmdline
import datetime
# 获取指定日期内的所有帖子

# cmd = 'scrapy crawl allcontent'
cmd = 'scrapy crawl single_user'
cmdline.execute(cmd.split())