# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2019/7/10 22:46
# @File : guess_first_day_price.py

# 猜测第一天上市价格
# 使用twsisted失败

from twisted.web.client import getPage
from twisted.internet import reactor
from twisted.internet import defer
from scrapy.selector import Selector
import numpy as np

result_list = []

def get_response_callback(content):
    # print(content)

    text = str(content,encoding='utf-8')
    # print(text)
    response = Selector(text=text)
    nodes = response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div')
    for node in nodes:
        reply = node.xpath('.//div[@class="markitup-box"]/text()').extract_first()
        if reply:
            reply = reply.strip()
            # print(reply)
            result_list.append(float(reply))

    print('done')


@defer.inlineCallbacks
def task(url):
    d= getPage(url.encode('utf-8'))
    d.addCallback(get_response_callback)
    yield d

def get_result():
    # print(result_list)
    # print(result_list)
    result = np.array(result_list)
    print(result.mean())

urls='https://www.jisilu.cn/question/id-321075__sort_key-__sort-DESC__uid-__page-{}'
d_list=[]
page = 4
for i in range(1,page+1):
    # print(urls.format(i))
    t = task(urls.format(i))
    # t = task(urls)
    d_list.append(t)
d = defer.DeferredList(d_list)
# d.addBoth(lambda _:reactor.callLater(0,get_result()))
d.addBoth(lambda _:reactor.stop())
reactor.run()

