# -*- coding: utf-8 -*-
import datetime
import logging
import re
import scrapy
from jsl.items import JslItem
from jsl import config
from jsl.spiders.aes_encode import decoder
from scrapy import Request,FormRequest
# 获取某个用户的所有帖子，主要为了慎防大v要删帖，快速下载

class JisiluSpider(scrapy.Spider):
    name = 'single_user'
    DETAIL_URL = 'https://www.jisilu.cn/question/{}&sort_key=agree_count&sort=DESC'
    MULTI_PAGE_DETAIL = 'https://www.jisilu.cn/question/id-{}__sort_key-__sort-DESC__uid-__page-{}'

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

        # self.uid = '83220'  # 这个id需要在源码页面里面去找
        self.uid = config.uid

        self.list_url =  'https://www.jisilu.cn/people/ajax/user_actions/uid-{}__actions-101__page-{}'


    def start_requests(self):

        login_url = 'https://www.jisilu.cn/login/'
        headersx = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,br', 'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
            'Host': 'www.jisilu.cn', 'Pragma': 'no-cache', 'Referer': 'https://www.jisilu.cn/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36'}

        yield Request(url=login_url, headers=headersx, callback=self.login, dont_filter=True)

    def login(self, response):
        url = 'https://www.jisilu.cn/account/ajax/login_process/'
        username = decoder(config.jsl_user)
        jsl_password = decoder(config.jsl_password)
        data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': username,
            'password': jsl_password,
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }

        yield FormRequest(
            url=url,
            headers=self.headers,
            formdata=data,
            callback=self.start_fetch_user,
            dont_filter=True,

        )


    def start_fetch_user(self,response):
        current_page=0
        yield scrapy.Request(self.list_url.format(self.uid,current_page),headers=self.headers,meta={'current_page':current_page},callback=self.parse)

    def parse(self, response,**kwargs):
        current_page = response.meta['current_page']
        link_list = response.xpath('//body/div[@class="aw-item"]')
        if link_list is None:
            return

        for link in link_list:
            link_=link.xpath('.//div[@class="aw-mod"]/div[@class="aw-mod-head"]/h4/a/@href').extract_first()
            match = re.search('/question/(\d+)',link_)
            if match:
                question_id = match.group(1)
                yield scrapy.Request(self.DETAIL_URL.format(question_id),
                                     headers=self.headers,
                                     callback=self.parse_item,
                                     meta={'question_id':question_id})

        current_page=current_page+1
        yield scrapy.Request(self.list_url.format(self.uid,current_page),headers=self.headers,meta={'current_page':current_page},callback=self.parse)


    def check_detail(self,response,**kwargs):

        if '您访问的资源需要购买会员' in response.text:
            return

        question_id = response.meta['question_id']
        more_page = response.xpath('//div[@class="pagination pull-right"]')

        item = JslItem()
        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()
        s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()
        ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)
        item['question_id'] = question_id

        try:
            content = ret[0].strip()
        except Exception as e:
            logging.error(e)
            content = None

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/div/span/text()').extract_first()
        # 'aw-question-detail-meta'
        resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

        url = response.url

        # 添加发起人
        try:
            item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
        except Exception as e:
            logging.error(e)
            item['creator'] = None

        item['title'] = title.strip()
        item['content'] = content
        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            # logging.warning('没有回复')
            item['resp_no'] = 0

        item['createTime'] = createTime.replace('发表时间 ', '')
        item['crawlTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item['url'] = url.strip()
        # item['html'] = response.text
        # item['last_resp_date'] = response.meta['last_resp_date']

        # 多页
        if more_page:

            total_resp_no = item['resp_no']
            total_page = total_resp_no // 100 + 1
            item['resp'] = []

            yield Request(url=self.MULTI_PAGE_DETAIL.format(question_id, 1), headers=self.headers,
                          callback=self.multi_page_detail,
                          meta={'question_id': question_id, 'page': 1, 'total_page': total_page,
                                'item': item})

        else:

            resp_ = []
            # 回复内容
            resp_time_list = []
            for index, reply in enumerate(
                    response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')):
                replay_user = reply.xpath(
                    './/div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()
                rep_content = reply.xpath(
                    './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]')[0].xpath(
                    'string(.)').extract_first()

                # 注意这里为了从用户初采集，加了这个字段
                rep_time = reply.xpath('.//div[@class="pull-left aw-dynamic-topic-content"]//div[@class="aw-dynamic-topic-meta"]/span/text()').extract_first()
                resp_time_list.append(rep_time)
                agree = reply.xpath('.//em[@class="aw-border-radius-5 aw-vote-count pull-left"]/text()').extract_first()
                if agree is None:
                    agree = 0
                else:
                    agree = int(agree)

                resp_.append(
                    {replay_user.strip(): {'agree': agree, 'resp_content': rep_content.strip()}})
            if len(resp_time_list)>0:
                resp_time = resp_time_list[0]
            else:
                resp_time=None
            item['resp'] = resp_
            item['last_resp_date']=resp_time

            yield item

    # 详情页
    def multi_page_detail(self, response):

        current_page = response.meta['page']
        item = response.meta['item']
        total_page = response.meta['total_page']
        question_id = response.meta['question_id']

        resp_len = response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]/div')

        for index, reply in enumerate(
                response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')):
            replay_user = reply.xpath(
                './/div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()
            rep_content = reply.xpath(
                './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]')[0].xpath(
                'string(.)').extract_first()
            if rep_content:
                rep_content = rep_content.strip()
            # rep_content = '\n'.join(rep_content)

            agree = reply.xpath('.//em[@class="aw-border-radius-5 aw-vote-count pull-left"]/text()').extract_first()
            if agree is None:
                agree = 0
            else:
                agree = int(agree)

            item['resp'].append(
                {replay_user.strip(): {'agree': agree, 'resp_content': rep_content.strip()}})

        current_page += 1

        if current_page <= total_page:
            yield Request(url=self.MULTI_PAGE_DETAIL.format(question_id, current_page), headers=self.headers,
                          callback=self.multi_page_detail,
                          meta={'question_id': question_id, 'page': current_page, 'total_page': total_page,
                                'item': item})
        else:
            yield item