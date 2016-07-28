# -*- coding: utf-8 -*-
# this is a track of python calling log client/sender


from __future__ import absolute_import
import functools
import uuid
import traceback
import time
import simplejson as json
from tracking import msg_queue, logger


def track(func):
    functools.wraps(func)
    def _wrapper(*args, **kwargs):
        setattr(func, '__track__', True)
        result = func(*args, **kwargs)
        delattr(func, '__track__')
        return result
    return _wrapper


class Tracker(object):
    def __init__(self, chain_id=None, chain_name=None):
        """ begin to track
        :param chain_name: name of method calling chain
        :return:
        """
        self.__seq = -1
        self.chain_id = chain_id or uuid.uuid4()
        self.chain_name = chain_name or chain_id

    @property
    def _seq(self):
        self.__seq += 1
        return self.__seq

    def tracking(self, desc=None, exception=None, return_value=None):
        """ track the calling chain list
        :param desc: description message of what you are tracking
        :param exception: when catch the exception you can pass it to track
        :param return_value: method return value you want to monitor
        :return:
        """
        self.__send(desc,exception,return_value)

    def __send(self, desc=None, exception=None, return_value=None, track_finished=False):
        exc_message = None
        exc_info = None
        if not exception:
            assert isinstance(exception, Exception)
            exc_message = exception.message
            exc_info = traceback.format_exc()
        message_formater = {
            'chain_id': self.chain_id,
            'seq': self._seq,
            'chain_name': self.chain_name,
            'desc': desc,
            'exception_message': exc_message,
            'exception_stack': exc_info,
            'return_value': return_value,
            'track_finished': track_finished,
            'timestamp': int(time.time() * 1000)
        }
        logger.debug("tracker put message in queue %s", json.dumps(message_formater))
        msg_queue.put(message_formater)

    def __del__(self):
        """
        track finish
        :return:
        """
        self.__send(track_finished=True)
        pass
