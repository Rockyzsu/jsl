# -*- coding: utf-8 -*-
import re

import scrapy
from jsl.items import JslItem

class JisiluSpider(scrapy.Spider):
    name = 'jisilu'

    def __init__(self):
        super(JisiluSpider,self).__init__()

        self.headers = {
                        'Accept-Language': ' zh-CN,zh;q=0.9', 'Accept-Encoding': ' gzip, deflate, br',
                        'X-Requested-With': ' XMLHttpRequest', 'Host': ' www.jisilu.cn', 'Accept': ' */*',
                        'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36',
                        'Connection': ' keep-alive',
                        'Pragma': ' no-cache', 'Cache-Control': ' no-cache',
                        'Referer': ' https://www.jisilu.cn/people/dbwolf'
                        }
        self.uid = '83220'  # 这个id需要在源码页面里面去找
    def start_requests(self):
        url = 'https://www.jisilu.cn/people/ajax/user_actions/uid-{}__actions-101__page-{}'
        for num in range(0, 100):
            yield scrapy.Request(url.format(self.uid,num),headers=self.headers)

    def parse(self, response):
        link_list = response.xpath('//div[@class="aw-item"]//h4/a/@href').extract()
        for i in link_list:
            yield scrapy.Request(i,headers=self.headers,callback=self.parse_item)

    def parse_item(self,response):
        item = JslItem()
        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract()[0]
        s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract()[0]
        ret = re.findall('(.*?)\.donate_user_avatar',s,re.S)
        try:
            content = ret[0].strip()
        except:
            content = 'NULL'

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/span/text()').extract_first()

        url = response.url
        item['title']=title.strip()
        item['content']= content
        item['createTime'] = createTime
        item['url'] = url.strip()
        resp = []
        for reply in response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]'):


            replay_user = reply.xpath('.//div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()
            rep_content = reply.xpath('.//div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]/text()').extract_first()
            # print rep_content
            resp.append((replay_user.strip(),rep_content.strip()))


        item['resp']=resp

        yield item