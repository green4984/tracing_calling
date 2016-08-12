# -*- coding: utf-8 -*-
"""
monkey patch for support lib
"""

from __future__ import absolute_import
from tracking.import_hook import register_import_hook, module_import_hook

__all__ = [
    'patch_all'
]

_module_import_hook_registry = {}


def patch_all():
    patch_module('requests.api', 'tracking.hooks.requests', 'tracking_hook_request_api')


def patch_module(target, module, function):
    """ hook module, wrap the real function call like decorator
    :param target:
    :param module:
    :param function:
    :return:
    """
    if target in _module_import_hook_registry:
        return
    _module_import_hook_registry.setdefault(target, None)
    register_import_hook(target, module_import_hook(module, function))
