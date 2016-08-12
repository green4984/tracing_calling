# -*- coding: utf-8 -*-

from __future__ import absolute_import
import sys

# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
formater = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formater)
logger.setLevel(logging.DEBUG)
logger.addHandler(console)

from .import_hook import ImportHookFinder

sys.meta_path.insert(0, ImportHookFinder())

from multiprocessing import Queue

msg_queue = Queue()

from .main import track, Tracker, TrackerManager, RedisAdaptor
from .tracking_context import LocalProxy

current_tracker = LocalProxy()
