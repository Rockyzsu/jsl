# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging


# 遍历所有questions id 看从哪里开始
class AllcontentSpider(scrapy.Spider):
    name = 'questions'

    headers = {
        'Host': 'www.jisilu.cn', 'Connection': 'keep-alive', 'Pragma': 'no-cache',
        'Cache-Control': 'no-cache', 'Accept': 'application/json,text/javascript,*/*;q=0.01',
        'Origin': 'https://www.jisilu.cn', 'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Referer': 'https://www.jisilu.cn/login/',
        'Accept-Encoding': 'gzip,deflate,br',
        'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8'
    }

    def start_requests(self):
        login_url = 'https://www.jisilu.cn/login/'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,br', 'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8',
            'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
            'Host': 'www.jisilu.cn', 'Pragma': 'no-cache', 'Referer': 'https://www.jisilu.cn/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36'}

        yield Request(url=login_url, headers=headers, callback=self.login, dont_filter=True)

    def login(self, response):
        url = 'https://www.jisilu.cn/account/ajax/login_process/'
        data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': config.jsl_user,
            'password': config.jsl_password,
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }

        yield FormRequest(
            url=url,
            headers=self.headers,
            formdata=data,
            callback=self.parse,
        )

    def parse(self, response):
        lastest_id = config.LASTEST_ID  # 394716

        for i in range(lastest_id + 5000, 1, -1):
            focus_url = 'https://www.jisilu.cn/question/{}'.format(i)
            yield Request(url=focus_url, headers=self.headers, callback=self.parse_item, meta={'question_id': str(i)})

    def parse_item(self, response):
        item = JslItem()
        question_id = response.meta['question_id']

        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()
        s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()

        if s:
            ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)
        else:
            ret = None

        try:
            content = ret[0].strip()
        except:
            content = None

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/div/span/text()').extract_first()
        if createTime is None:
            return

        resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

        url = response.url

        # 添加发起人
        try:
            item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
        except Exception as e:
            print(e)
            item['creator'] = None


        try:
            title = title.strip()
        except Exception as e:
            title = None
        item['content'] = content
        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            logging.warning(e)
            logging.warning('没有回复')
            item['resp_no'] = 0
        item['title'] = title
        item['question_id'] = question_id

        createTime = createTime.strip()

        if not re.search('^\d', createTime):
            createTime = createTime.replace('发表时间 ', '')
            # createTime = None
            # self.logger.error('创建日期有误:{}'.format(url))
        if not re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}', createTime):
            self.logger.error('创建日期有误:{}'.format(url))
            self.logger.error(createTime)
            createTime = None
        #
        item['createTime'] = createTime
        item['url'] = url.strip()
        resp = []
        last_resp_date = None
        for index, reply in enumerate(
                response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')):
            replay_user = reply.xpath('.//div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()

            if last_resp_date is None:
                last_resp_date = reply.xpath('.//div[@class="aw-dynamic-topic-meta"]/span/text()').extract_first()

            rep_content = reply.xpath(
                './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]/text()').extract_first()
            # print rep_content
            agree = reply.xpath('.//em[@class="aw-border-radius-5 aw-vote-count pull-left"]/text()').extract_first()
            try:
                int(agree)
            except:
                agree = 0

            resp.append({replay_user.strip() + '_{}'.format(index): [int(agree), rep_content.strip()]})
        # item['html'] = response.text
        item['crawlTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        item['resp'] = resp
        item['last_resp_date'] = last_resp_date
        item['only_add'] = True
        yield item
