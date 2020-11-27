# -*- coding: utf-8 -*-
# @Time : 2020/11/27 22:00
# @File : aes_encode.py
# @Author : Rocky C@www.30daydo.com

import execjs
import os
key = '397151C04723421F'
filename = '集思录.js'
path = os.path.dirname(os.path.abspath(__file__))
full_path = os.path.join(path,filename)

def decoder(text):
    with open(full_path, 'r', encoding='utf8') as f:
        source = f.read()

    ctx = execjs.compile(source)
    return ctx.call('jslencode', text, key)


if __name__ == '__main__':
    print(decoder('123456'))