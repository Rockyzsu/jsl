# -*- coding: utf-8 -*-
# website: http://30daydo.com
# @Time : 2019/10/20 19:41
# @File : guess_first_day_price_syncup.py

# 同步获取
import requests
import time
from selenium import webdriver
from scrapy.selector import Selector
import config

import pymongo



headers = {'User-Agent': 'FireFox Molliza Chrome'}
path = r'D:\OneDrive\Python\selenium\chromedriver.exe'
option = webdriver.ChromeOptions()
option.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 9.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36')
option.add_argument('--headless')
driver = webdriver.Chrome(executable_path=path, chrome_options=option)
driver.implicitly_wait(10)


def login():
    url = 'https://www.jisilu.cn/login/'
    driver.get(url)
    input_name = driver.find_element_by_xpath('//input[@id="aw-login-user-name"]')
    input_name.send_keys(config.jsl_user)
    password = driver.find_element_by_xpath('//input[@id="aw-login-user-password"]')
    password.send_keys(config.jsl_password)
    time.sleep(0.5)
    submit = driver.find_element_by_xpath('//a[@id="login_submit"]')
    submit.click()
    time.sleep(5)


def predict(url,name):

    driver.get(url)
    current_page = 1
    count = 0
    sum = 0
    while 1:

        try:

            price = parse(driver.page_source)
            if price:
                count += 1
                sum = sum + price

            next_btn = driver.find_element_by_xpath('//div[@class="pagination pull-right"]//a[contains(text(),">")]')

        except Exception as e:
            break
        else:

            current_page += 1
            next_btn.click()

    avg = round(sum / count,3)
    print(f'avg price {avg}')
    client = pymongo.MongoClient(config.mongodb_host, config.mongodb_port)
    doc = client['db_stock']['kzz_price_predict']
    doc.insert_one({'name':name,'predict_price':avg})
    driver.close()


def parse(text):
    response = Selector(text=text)
    nodes = response.xpath('//div[@class="aw-mod-body aw-dynamic-topic"]/div[@class="aw-item"]')
    for node in nodes:
        comment = node.xpath(
            './/div[@class="pull-left aw-dynamic-topic-content"]//div[@class="markitup-box"]/text()').extract_first()
        if comment:
            comment = comment.strip()
            try:
                comment = float(comment)
                return comment
            except Exception as e:
                return None

        else:
            return None


def main():
    login()

    url = 'https://www.jisilu.cn/question/330663'
    name='合兴转债'
    predict(url,name)

if __name__ == '__main__':
    main()
