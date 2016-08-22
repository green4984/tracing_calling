# -*- coding: utf-8 -*-
import time
import abc
from tracking import (current_tracker as tracker, logger)

class TimeTrace(object):
    def __init__(self):
        self.tracing = tracker._is_tracking
        self.start_time = 0
        self.end_time = 0
        self.duration = 0
        self._desc = None

    @property
    def _curr_time(self):
        """ get current timestamp of microsecond
        :return: current time microsecond
        """
        return int(time.time() * 1000)

    def __enter__(self):
        if not self.tracing:
            return self

        if not tracker._is_tracking:
            return self

        self.start_time = self._curr_time
        tracker.tracking_begin(desc=self._desc, bgn=self.start_time)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.tracing:
            return
        if not tracker._is_tracking:
            return

        error = exc_val
        if exc_tb:
            logger.error("catch error %s", exc_val.message)
        self.end_time = self._curr_time
        self.duration = self.end_time - self.start_time
        logger.debug("duration %d", self.duration)
        msg = tracker.tracking_end(exc_val, depth=7, end=self.end_time, duration=self.duration, handle_func=self.handle_msg)

    ##################################
    ## need derive class realize it ##
    ##################################
    def handle_msg(self, msg):
        return msg
