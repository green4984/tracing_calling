# -*- coding: utf-8 -*-
from tracking import monkey; monkey.patch_request()
import tracking

import requests
from function_call import register_tracker, unregister_tracker


def length_html(data):
    print len(data)
    return len(data)

@tracking.track
def request_url(url):
    try:
        r = requests.get(url)
        r = requests.request('GET', url)
        return length_html(r.text)
    except Exception as e:
        pass
    return 0

def request_url_with_log(url):
    r = requests.get(url)
    r = requests.request('GET', url)
    return length_html(r.text)

url_list = [
    'http://www.exampleasdfasdfasdf.com/',
    'http://www.example.net',
    'http://www.example.org'
]


register_tracker([
    [__file__, 'request_url'],
    [__file__, 'length_html']
])

request_url(url_list[0])

unregister_tracker([
    [__file__, 'request_url'],
    [__file__, 'length_html']
])

request_url(url_list[1])
