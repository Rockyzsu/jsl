# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging
from jsl.spiders.aes_encode import decoder
import pymongo

# 按照日期爬取, 会损失新人贴

class WeekContentSpider(scrapy.Spider):
    name = 'week_content'

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

    POST_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-add_time__category-__day-0__is_recommend-__page-{}'  # 发帖日期
    RESP_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-new__category-__day-0__is_recommend-__page-{}'  # 回帖按照日期
    DETAIL_URL = 'https://www.jisilu.cn/question/{}&sort_key=agree_count&sort=DESC'
    MULTI_PAGE_DETAIL = 'https://www.jisilu.cn/question/id-{}__sort_key-__sort-DESC__uid-__page-{}'

    def __init__(self, daily='yes', *args, **kwargs):
        super().__init__(*args, **kwargs)

        if daily == 'yes':

            self.logger.info('按照周')
            self.DAYS = 14  # 获取2年的帖子
            self.URL = self.POST_DATE_URL

        self.last_week = datetime.datetime.now() + datetime.timedelta(days=-1 * self.DAYS)


        connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
        self.db = pymongo.MongoClient(connect_uri)
        # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
        self.collection = self.db['db_parker'][config.doc_name]

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
            callback=self.parse,
            dont_filter=True
        )

    def parse(self, response, **kwargs):
        print('登录后', response.text)
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
                logging.error('failed to find date')
                continue
            else:
                # 访问详情
                # 替换成这个 'https://www.jisilu.cn/question/320215&sort_key=agree_count&sort=DESC'
                # '"https://www.jisilu.cn/question/336326"'
                if re.search('www.jisilu.cn/question/\d+', each_url):
                    question_id = re.search('www\.jisilu\.cn/question/(\d+)', each_url).group(1)

                    # if self.question_exist(question_id):
                        # continue

                    # print(f'{question_id}帖子不存在，下载')

                    last_resp_date = datetime.datetime.strptime(last_resp_date, '%Y-%m-%d %H:%M')
                    yield Request(url=self.DETAIL_URL.format(question_id), headers=self.headers,
                                  callback=self.check_detail,
                                  meta={'last_resp_date': last_resp_date, 'question_id': question_id})

        # 继续翻页
        # print(last_resp_date)
        if last_resp_date is not None and isinstance(last_resp_date,str):
            last_resp_date = datetime.datetime.strptime(last_resp_date, '%Y-%m-%d %H:%M')

        if last_resp_date is not None and (self.last_week < last_resp_date):
            # logging.info('last_resp_date ===== {}'.format(last_resp_date))

            current_page += 1
            yield Request(url=self.URL.format(current_page), headers=self.headers, callback=self.parse_page,
                          meta={'page': current_page})

    def question_exist(self,_id):
        return True if self.collection.find_one({'question_id':_id},{'_id':1}) else False

    def compose_content(self,content_list):
        string = ""
        for line in content_list:
            line = line.strip()
            if len(line)>0:
                string+=line+'\n'
        return string

    def check_detail(self, response):

        if '您访问的资源需要购买会员' in response.text:
            return

        question_id = response.meta['question_id']
        last_resp_date=response.meta['last_resp_date']
        more_page = response.xpath('//div[@class="pagination pull-right"]')

        item = JslItem()
        item['last_resp_date'] = last_resp_date

        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()
        item['question_id'] = question_id
        content_node = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]')

        content_html = content_node.extract_first() # 获取到源码

        # s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()
        # ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)
        # try:
        #     content = ret[0].strip()
        # except Exception as e:
        #     # logging.error(e)
        #     content = None

        content_list = content_node.xpath('string(.)').extract()
        content_str = self.compose_content(content_list)

        createTime = response.xpath('//div[@class="aw-question-detail-meta"]/div/span/text()').extract_first()
        # 'aw-question-detail-meta'
        resp_no = response.xpath('//div[@class="aw-mod aw-question-detail-box"]//ul/h2/text()').re_first('\d+')

        url = response.url

        # 添加发起人
        try:
            item['creator'] = response.xpath('//div[@class="aw-side-bar-mod-body"]/dl/dd/a/text()').extract_first()
        except Exception as e:
            # logging.error(e)
            item['creator'] = None

        item['title'] = title.strip()
        item['content'] = content_str
        item['content_html'] = content_html

        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            # logging.warning('没有回复')
            item['resp_no'] = 0
        if createTime is None:
            # print(title)
            # print(content)
            return
        item['createTime'] = createTime.replace('发表时间 ', '')
        item['crawlTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        item['url'] = url.strip().replace('&sort_key=agree_count&sort=DESC','')

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

        for index, reply in enumerate(
                response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')):
            replay_user = reply.xpath(
                './/div[@class="pull-left aw-dynamic-topic-content"]//p/a/text()').extract_first()
            rep_content = reply.xpath(
                './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]')[0].xpath(
                'string(.)').extract_first()
            if rep_content:
                rep_content = rep_content.strip()

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
