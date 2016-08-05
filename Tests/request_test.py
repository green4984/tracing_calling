# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from tracking import monkey; monkey.patch_request()
from tracking import current_tracker as tracker
import tracking

import requests
import time
import random
from function_call import register_tracker, unregister_tracker

track_manager = tracking.TrackerManager(tracking.RedisAdaptor, redis_uri='redis://localhost:6380/3')

def length_html(data):
    print len(data)
    return len(data)

@tracking.track
def request_url(url):
    try:
        time.sleep(random.random())
        r = requests.get(url)
        length = length_html(r.text)
        return length
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


# register_tracker([
#     [__file__, 'request_url'],
#     [__file__, 'length_html']
# ])

request_url(url_list[0])

# unregister_tracker([
#     [__file__, 'request_url'],
#     [__file__, 'length_html']
# ])

request_url(url_list[1])
request_url_with_log(url_list[1])
