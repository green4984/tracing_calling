# -*- coding: utf-8 -*-
from .external_trace import ExternalTrace
from ..packages.wrapt import (FunctionWrapper as _FunctionWrapper,
                              BoundFunctionWrapper as _BoundFunctionWrapper)

def ExternalTraceWrapper(wrapped, library, url):
    def _wrapper(wrapped, instance, args, kwargs):
        if callable(url):
            if instance:
                _url = url(instance, *args, **kwargs)
            else:
                _url = url(*args, **kwargs)
        else:
            _url = url
        with ExternalTrace(library, _url):
            return wrapped(*args, **kwargs)

    return FunctionWrapper(wrapped, _wrapper)

class _OABoundFunctionWrapper(_BoundFunctionWrapper):
    pass

class FunctionWrapper(_FunctionWrapper):
    __bound_function_wrapper__ = _OABoundFunctionWrapper

