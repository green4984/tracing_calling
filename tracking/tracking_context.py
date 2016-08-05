# -*- coding: utf-8 -*-
"""
thread ident as key save it in thread.local
"""
import threading
from .main import TrackerManager, Tracker


__all__ = [
    'LocalProxy'
]

_local = threading.local()

class LocalProxy(object):
    def __init__(self):
        self.__ident = str(threading.current_thread().ident)

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
        tracker = Tracker(chain_name=name)
        setattr(self._local, '__tracker__', tracker)

    def _unhook(self):
        tracker = getattr(self._local, '__tracker__', None)
        if tracker:
            delattr(self._local, '__tracker__')
            del tracker

    def _is_tracking(self):
        if self._local:
            return True
        return False

    def __getattr__(self, name):
        if name in ('_hook', '_unhook', '_local', '_is_tracking'):
            return getattr(self, name)
        tracker = getattr(self._local, '__tracker__', None)
        if tracker:
            return getattr(tracker, name)
