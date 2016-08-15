# -*- coding: utf-8 -*-
from .time_trace import TimeTrace


class ExternalTrace(TimeTrace):
    def __init__(self, library, url):
        super(ExternalTrace, self).__init__()
