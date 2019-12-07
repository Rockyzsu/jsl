# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging

DAYS = 2


class AllcontentSpider(scrapy.Spider):
    name = 'allcontent'

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

    start_page = 1

    last_week = datetime.datetime.now() + datetime.timedelta(days=-1 * DAYS)

    URL = 'https://www.jisilu.cn/home/explore/sort_type-add_time__category-__day-0__is_recommend-__page-{}'

    DETAIL_URL = 'https://www.jisilu.cn/question/{}&sort_key=agree_count&sort=DESC'
    MULTI_PAGE_DETAIL = 'https://www.jisilu.cn/question/id-{}__sort_key-__sort-DESC__uid-__page-{}'

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
            dont_filter=True
        )

    def parse(self, response):

        focus_url = self.URL.format(self.start_page)

        yield Request(url=focus_url, headers=self.headers, callback=self.parse_page, dont_filter=True,
                      meta={'page': self.start_page})

    def parse_page(self, response):

        current_page = response.meta['page']

        nodes = response.xpath('//div[@class="aw-question-list"]/div')
        last_resp_date = None

        for node in nodes:
            each_url = node.xpath('.//h4/a/@href').extract_first()
            try:
                last_resp_date = node.xpath('.//div[@class="aw-questoin-content"]/span/text()').extract()[-1].strip()
                # '回复  • 2018-12-10 09:49 • 46335 次浏览'
                last_resp_date = re.search('• (.*?) •', last_resp_date).group(1)
            except:
                last_resp_date = None
                print('failed to find date')

            else:
                # 访问详情
                # 替换成这个 'https://www.jisilu.cn/question/320215&sort_key=agree_count&sort=DESC'
                # '"https://www.jisilu.cn/question/336326"'
                if re.search('www.jisilu.cn/question/\d+', each_url):
                    question_id = re.search('www.jisilu.cn/question/(\d+)', each_url).group(1)

                    yield Request(url=self.DETAIL_URL.format(question_id), headers=self.headers,
                                  callback=self.check_detail, dont_filter=True,
                                  meta={'last_resp_date': last_resp_date, 'question_id': question_id})

        last_resp_date_dt = datetime.datetime.strptime(last_resp_date, '%Y-%m-%d %H:%M')

        # 继续翻页
        if self.last_week < last_resp_date_dt:
            current_page += 1
            yield Request(url=self.URL.format(current_page), headers=self.headers, callback=self.parse_page,
                          dont_filter=True, meta={'page': current_page})

    def check_detail(self, response):
        question_id = response.meta['question_id']
        more_page = response.xpath('//div[@class="pagination pull-right"]')
        last_resp_date = response.meta['last_resp_date']

        item = JslItem()
        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()
        s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()
        ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)
        item['question_id'] = question_id

        try:
            content = ret[0].strip()
        except:
            content = None

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/div/span/text()').extract_first()
        # 'aw-question-detail-meta'
        resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

        url = response.url

        # 添加发起人
        try:
            item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
        except Exception as e:
            print(e)
            item['creator'] = None

        item['title'] = title.strip()
        item['content'] = content
        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            # logging.warning(e)
            logging.warning('没有回复')
            item['resp_no'] = 0

        item['createTime'] = createTime.replace('发表时间 ', '')
        item['crawlTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item['url'] = url.strip()
        item['html'] = response.text
        item['last_resp_date'] = response.meta['last_resp_date']

        # 多页
        if more_page:

            total_resp_no = item['resp_no']
            total_page = total_resp_no//100+1
            item['resp']=[]

            yield Request(url=self.MULTI_PAGE_DETAIL.format(question_id, 1), headers=self.headers,
                              callback=self.multi_page_detail, dont_filter=True,
                              meta={'question_id': question_id, 'page': 1,'total_page':total_page,
                                    'item': item})

        else:

            resp_=[]
            # 回复内容
            for index, reply in enumerate(
                    response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')):
                replay_user = reply.xpath(
                    './/div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()
                rep_content = reply.xpath(
                    './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]')[0].xpath(
                    'string(.)').extract_first()
                # rep_content = '\n'.join(rep_content)

                agree = reply.xpath('.//em[@class="aw-border-radius-5 aw-vote-count pull-left"]/text()').extract_first()
                if agree is None:
                    agree = 0
                else:
                    agree = int(agree)

                resp_.append(
                    {replay_user.strip(): {'agree': agree, 'resp_content': rep_content.strip()}})

            item['resp'] = resp_

            yield item

    # 详情页

    def multi_page_detail(self, response):

        current_page = response.meta['page']
        item = response.meta['item']
        total_page = response.meta['total_page']
        question_id = response.meta['question_id']

        resp_len = response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]/div')
        print('本页回复数目{}'.format(len(resp_len)))

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

        current_page+=1

        if current_page<=total_page:
            print(f'页码{current_page}/{total_page}')
            yield Request(url=self.MULTI_PAGE_DETAIL.format(question_id, current_page), headers=self.headers,
                              callback=self.multi_page_detail, dont_filter=True,
                              meta={'question_id': question_id, 'page': current_page,'total_page':total_page,
                                    'item': item})
        else:
            yield item
