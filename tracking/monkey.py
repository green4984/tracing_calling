# -*- coding: utf-8 -*-
"""
monkey patch for support lib
"""

from __future__ import absolute_import

__all__ = [
    'patch_request'
]

saved = {}

def patch_request():
    """ Just for patch requests python lib for tracing operation
    :return None
    """
    patch_module('requests')


def patch_module(name):
    if name in saved:
        return
    inner_lib_module = getattr(__import__('tracking.' + name), name)
    module_name = getattr(inner_lib_module, '__target__', name)
    module = __import__(module_name)
    implements = getattr(inner_lib_module, '__implements__', [])
    for attr in implements:
        setattr(module, attr, getattr(inner_lib_module, attr))
    saved.setdefault(name, None)
