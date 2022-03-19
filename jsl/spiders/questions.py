# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy import Request, FormRequest
from jsl.items import JslItem
from jsl import config
import logging
import pymongo

# 遍历所有questions id 看从哪里开始
class QuestionSpider(scrapy.Spider):
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

    POST_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-add_time__category-__day-0__is_recommend-__page-{}'  # 发帖日期
    RESP_DATE_URL = 'https://www.jisilu.cn/home/explore/sort_type-new__category-__day-0__is_recommend-__page-{}'  # 回帖按照日期
    DETAIL_URL = 'https://www.jisilu.cn/question/{}&sort_key=agree_count&sort=DESC'
    MULTI_PAGE_DETAIL = 'https://www.jisilu.cn/question/id-{}__sort_key-__sort-DESC__uid-__page-{}'

    # self.doc =
    connect_uri = f'mongodb://{config.user}:{config.password}@{config.mongodb_host}:{config.mongodb_port}'
    db = pymongo.MongoClient(connect_uri)
    # self.user = u'neo牛3' # 修改为指定的用户名 如 毛之川 ，然后找到用户的id，在用户也的源码哪里可以找到 比如持有封基是8132
    # self.collection = self.db['db_parker']['jsl_20181108_allQuestion_test']
    collection = db['db_parker'][config.doc_name]

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

    def question_exist(self,_id):
        return True if self.collection.find_one({'question_id':_id},{'_id':1}) else False

    def parse(self, response,**kwargs):
        lastest_id = config.LASTEST_ID  #

        for i in range(lastest_id + 5000, 1, -1):
            if not self.question_exist(lastest_id):
                focus_url = 'https://www.jisilu.cn/question/{}'.format(i)
                yield Request(url=focus_url, headers=self.headers, callback=self.parse_item, meta={'question_id': str(i)})
    def compose_content(self,content_list):
        string = ""
        for line in content_list:
            line = line.strip()
            if len(line)>0:
                string+=line+'\n'
        return string

    def parse_item(self, response):
        item = JslItem()
        question_id = response.meta['question_id']

        title = response.xpath('//div[@class="aw-mod-head"]/h1/text()').extract_first()

        # s = response.xpath('//div[@class="aw-question-detail-txt markitup-box"]').xpath('string(.)').extract_first()

        # if s:
        #     ret = re.findall('(.*?)\.donate_user_avatar', s, re.S)
        # else:
        #     ret = None

        # try:
        #     content = ret[0].strip()
        # except:
        #     content = None


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

        item['content'] = content_str

        item['content_html'] = content_html

        try:
            item['resp_no'] = int(resp_no)
        except Exception as e:
            # logging.warning(e)
            # logging.warning('没有回复')
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
        item['url'] = url.strip().replace('&sort_key=agree_count&sort=DESC','')

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

    def check_detail(self, response):

        if '您访问的资源需要购买会员' in response.text:
            return

        question_id = response.meta['question_id']
        more_page = response.xpath('//div[@class="pagination pull-right"]')

        item = JslItem()
        last_resp_date = None # 后期更新

        item['last_resp_date'] = last_resp_date
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
        item['last_resp_date'] = response.meta['last_resp_date']

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
