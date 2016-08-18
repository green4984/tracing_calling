# -*- coding: utf-8 -*-
import time
import abc
from tracking import current_tracker, logger

class TimeTrace(object):
    def __init__(self):
        self.tracing = current_tracker._is_tracking
        self.start_time = 0
        self.end_time = 0
        self.duration = 0

    @property
    def _curr_time(self):
        """ get current timestamp of microsecond
        :return: current time microsecond
        """
        return int(time.time() * 1000)

    def __enter__(self):
        if not self.tracing:
            return self

        if not current_tracker._is_tracking:
            return self

        self.start_time = self._curr_time

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.tracing:
            return
        if not current_tracker._is_tracking:
            return

        self.end_time = self._curr_time
        self.duration = self.end_time - self.start_time
        logger.debug("duration %d", self.duration)
