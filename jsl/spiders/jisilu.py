# -*- coding: utf-8 -*-
import re

import scrapy
from jsl.items import JslItem

class JisiluSpider(scrapy.Spider):
    name = 'jisilu'
    allowed_domains = ['jisilu.cn']

    # start_urls = ['http://jisilu.cn/']

    def __init__(self):
        self.headers = {
                        'Accept-Language': ' zh-CN,zh;q=0.9', 'Accept-Encoding': ' gzip, deflate, br',
                        'X-Requested-With': ' XMLHttpRequest', 'Host': ' www.jisilu.cn', 'Accept': ' */*',
                        'User-Agent': ' Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36',
                        'Connection': ' keep-alive',
                        # 'Cookie': ' kbzw_r_uname=30%E5%A4%A9%E6%96%B0%E4%BA%8B%E6%83%85; kbz_newcookie=1; kbzw__Session=ka39tms3e8gutu6o00uvdb9ak4; Hm_lvt_164fe01b1433a19b507595a43bf58262=1525919695,1526092553,1526116515,1527398327; kbzw__user_login=7Obd08_P1ebax9aXqpJbBSBdCShFKuxa_PqKtJnnw-nU7ubl3L_NjKfe25ut0duWqJfd2aqqmNKZq62porCh3MbYk9jd1qjGkZyh7t7N18milK2TqLCpmZydtrXX0pTG2_HL4s3YpqimkZCJy-Ljzejj6oLEtZetoamckLjd56udtIzvmKqKl7jj6M3VuNnbwNLtm6yVrY-qrZOgrLi1wcWhieXV4seWqNza3ueKkKTc6-TW3putl6SRpaqmqpaekqqrlbza0tjU35CsqqqmlKY.; Hm_lpvt_164fe01b1433a19b507595a43bf58262=1527402958',
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