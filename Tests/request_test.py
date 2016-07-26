# -*- coding: utf-8 -*-
import requests
from gevent import monkey
monkey.patch_socket()
from function_call import register_tracker


def length_html(data):
    print len(data)
    return len(data)

def request_url(url):
    r = requests.get(url)
    return length_html(r.text)

url_list = [
    'https://www.360totalsecurity.com/',
    'http://www.baidu.com',
    'http://www.360.cn'
]

register_tracker([
    [__file__, 'request_url'],
    [__file__, 'length_html']
])

map(lambda x: request_url(x), url_list)
