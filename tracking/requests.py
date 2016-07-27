# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from tracking import logger as logging
import requests as _requests
import inspect

# save origin request for use
_request = _requests.request

__implements__ = [
    'request', 'get', 'head', 'post', 'patch', 'put', 'delete', 'options'
]


def request(method, url, **kwargs):
    logging.debug("request method %s url %s begin", method, url)
    response = None
    try:
        response = _request(method, url, **kwargs)
    except Exception as e:
        logging.error("request catch error %s", e.message, exc_info=1)
    finally:
        logging.debug("request method %s url %s end", method, url)
    return response


def get(url, params=None, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, params=params, **kwargs)


def options(url, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('options', url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request('post', url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request('patch', url,  data=data, **kwargs)


def delete(url, **kwargs):
    return request('delete', url, **kwargs)
