# -*- coding: utf-8 -*-
from tracking import monkey; monkey.patch_request()
import requests
from function_call import register_tracker


def length_html(data):
    print len(data)
    return len(data)

def request_url(url):
    r = requests.get(url)
    r = requests.request('GET', url)
    return length_html(r.text)

url_list = [
    'http://www.exampleasdfasdfasdf.com/',
    'http://www.example.net',
    'http://www.example.org'
]

# register_tracker([
#     [__file__, 'request_url'],
#     [__file__, 'length_html']
# ])

map(lambda x: request_url(x), url_list)
