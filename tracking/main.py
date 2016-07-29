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
        self.chain_id = chain_id or uuid.uuid4().get_hex()
        self.chain_name = chain_name or chain_id
        self.last_operation_timestamp = time.time()
        self.last_message = None

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
        self.__send(desc, exception, return_value)

    def __send(self, desc=None, exception=None, return_value=None, track_finished=False):
        exc_message = None
        exc_info = None
        if exception:
            assert isinstance(exception, Exception)
            exc_message = exception.message.message
            exc_info = traceback.format_exc()
        timestamp = int(time.time() * 1000)
        message_formater = {
            'chain_id': self.chain_id,
            'seq': self._seq,
            'chain_name': self.chain_name,
            'desc': desc,
            'exception_message': exc_message,
            'exception_stack': exc_info,
            'return_value': return_value,
            'track_finished': track_finished,
            'bgn_timestamp': timestamp,
            'end_timestamp': timestamp,
            'took': 0
        }

        if self.last_message: # has last message
            message_formater, self.last_message = self.last_message, message_formater

            if track_finished:
                message_formater['track_finished'] = True
            message_formater['end_timestamp'] = int(time.time() * 1000)
            message_formater['took'] = message_formater['end_timestamp'] - message_formater['bgn_timestamp']
            logger.debug("tracker put message in queue %s", json.dumps(message_formater))
            msg_queue.put(message_formater)
        else:
            self.last_message = message_formater

    def __del__(self):
        """
        track finish
        :return:
        """
        self.__send(track_finished=True)
        pass
