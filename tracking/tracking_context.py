# -*- coding: utf-8 -*-
"""
thread ident as key save it in thread.local
"""
import threading
from .main import Tracker
from tracking import logger

__all__ = [
    'LocalProxy'
]

_local = threading.local()


class LocalProxy(object):
    def __init__(self):
        self.__ident = str(threading.current_thread().ident)
        self.__is_tracking = 0

    def __enter__(self):
        self._hook()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._unhook()
        if exc_tb:
            logger.error("LocalProxy catch exception %s", exc_val.message)
            self.tracking(exception=exc_tb)
            raise

    @property
    def _local(self):
        global _local
        local = getattr(_local, self.__ident, None)
        if not local:
            local = threading.local()
            setattr(_local, self.__ident, local)
        return local

    @_local.setter
    def _local(self, value):
        local = self._local
        setattr(local, '__tracker__', value)

    def _hook(self, name=None):
        if self.__is_tracking == 0:
            tracker = Tracker(chain_name=name)
            setattr(self._local, '__tracker__', tracker)
        self.__is_tracking += 1

    def _unhook(self):
        if self.__is_tracking > 0:
            self.__is_tracking -= 1
        if self.__is_tracking > 0:
            return
        tracker = getattr(self._local, '__tracker__', None)
        if tracker:
            delattr(self._local, '__tracker__')
            del tracker

    @property
    def _is_tracking(self):
        return self.__is_tracking > 0

    def __getattr__(self, name):
        if name in ('_hook', '_unhook', '_local', '_is_tracking'):
            return getattr(self, name)
        tracker = getattr(self._local, '__tracker__', None)
        if tracker:
            return getattr(tracker, name)
