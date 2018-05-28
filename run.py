# -*-coding=utf-8-*-

__author__ = 'Rocky'
'''
http://30daydo.com
Email: weigesysu@qq.com
'''
from scrapy import  cmdline

def main():
    cmd = 'scrapy crawl jisilu'
    cmdline.execute(cmd.split())


if __name__ == '__main__':
    main()