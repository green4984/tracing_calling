# -*- coding: utf-8 -*-
from tracking import current_tracker
from .time_trace import TimeTrace


class ExternalTrace(TimeTrace):
    def __init__(self, library, url):
        super(ExternalTrace, self).__init__()
        self._desc = "%s %s" % (library, url)
        self.library = library
        self.url = url
