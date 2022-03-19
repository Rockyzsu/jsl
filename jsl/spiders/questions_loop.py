# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging

LASTEST_ID = config.LASTEST_ID  # 394716


# 遍历所有questions id 看从哪里开始
class AllcontentSpider(scrapy.Spider):
    name = 'questions_loop'

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
            callback=self.parse_,
        )

    def parse_(self, response):
        print(response.text)
        start_page = LASTEST_ID

        focus_url = 'https://www.jisilu.cn/question/{}'.format(start_page)
        yield Request(url=focus_url, headers=self.headers, callback=self.parse_item, meta={'question_id': start_page, 'dont_redirect': True,},
                      dont_filter=True)

    def parse_item(self, response):
        question_id_ = response.meta['question_id']

        if '问题不存在或已被删除' in response.text:
            question_id = question_id_ - 1
            if question_id>1:
                focus_url = 'https://www.jisilu.cn/question/{}'.format(question_id)

                yield Request(url=focus_url, headers=self.headers, callback=self.parse_item,
                              meta={'question_id': question_id, 'dont_redirect': True,}, dont_filter=True)

        else:

            question_id = question_id_ - 1
            print(question_id)
            if question_id > 1:
                focus_url = 'https://www.jisilu.cn/question/{}'.format(question_id)

                yield Request(url=focus_url, headers=self.headers, callback=self.parse_item,
                              meta={'question_id': question_id, 'dont_redirect': True,}, dont_filter=True)


            item = JslItem()

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

            resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

            url = response.url

            # 添加发起人
            try:
                item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
            except Exception as e:
                print(e)
                item['creator'] = None
            try:
                item['title'] = title.strip()
            except Exception as e:
                item['title']=None
            item['content'] = content

            if resp_no is None:
                resp_no = 0
            # try:
            #     item['resp_no'] = int(resp_no)
            # except Exception as e:
            #     logging.warning(e)
            #     logging.warning('没有回复')
            #     item['resp_no'] = None
            item['only_add'] = True
            item['resp_no'] = int(resp_no)
            item['question_id'] = question_id_
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

            item['resp'] = resp
            item['last_resp_date'] = last_resp_date

            yield item

