# -*-coding=utf-8-*-

# 抓取配置：pages 按列表页码抓取，days 保持原来的按日期抓取。
CRAWL_MODE = 'pages'
START_PAGE = 1
END_PAGE = 1  # 包含结束页；例如 3 和 5 表示抓取第 3、4、5 页。

from scrapy import cmdline
import datetime


def build_command():
    command = ['scrapy', 'crawl', 'allcontent', '-s',
               'LOG_FILE=log/allcontent-{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d')),
               '-a', 'daily=yes']
    if CRAWL_MODE == 'pages':
        command.extend(['-a', f'start_page={START_PAGE}', '-a', f'end_page={END_PAGE}'])
    elif CRAWL_MODE != 'days':
        raise ValueError("CRAWL_MODE 必须是 'pages' 或 'days'")
    return command


if __name__ == '__main__':
    cmdline.execute(build_command())
