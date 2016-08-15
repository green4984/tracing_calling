# -*- coding: utf-8 -*-
# this is a track of python calling log client/sender


from __future__ import absolute_import
import functools
import uuid
import traceback
import time
import simplejson as json
import Queue
from tracking import msg_queue, logger
import inspect
import atexit
import threading
from .store_adaptor import BaseAdaptor

__manager_status = False
_manager = None


def track(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        from tracking import current_tracker
        with current_tracker:
            # current_tracker.tracking(desc="call method %s" % repr(func.func_code))
            result = func(*args, **kwargs)
            return result

    return _wrapper


class TrackerManager(object):
    def __init__(self, adaptor_class, *args, **kwargs):
        global __manager_status
        __manager_status = True
        assert adaptor_class
        assert issubclass(adaptor_class, BaseAdaptor)
        self._cls = adaptor_class(*args, **kwargs)
        global _manager
        _manager = self._cls
        self.__init_send_thread()
        atexit.register(self.__receive_msg, exist_when_empty=True)

    def __init_send_thread(self):
        t = threading.Thread(target=self.__receive_msg)
        t.setDaemon(True)
        t.start()

    def __receive_msg(self, exist_when_empty=False):
        global __manager_status
        value = None
        while True:
            try:
                if not __manager_status:
                    logger.warning("exit send thread!!")
                    return
                value = msg_queue.get(timeout=10)
                self.__router(value)
                logger.debug("get data from msg_queue %s", value)
            except Queue.Empty as e:
                # logger.debug("get data from msg_queue empty %s", e.message, exc_info=1)
                pass
            if exist_when_empty and msg_queue.qsize() == 0:
                return

    def __router(self, value):
        if not self._cls.status():
            logger.error("%s connection error", self._cls)
            return
        action_dict = {
            'index': self.__save,
            'update': self.__update,
        }
        action = value.pop('_action', 'index')
        method = action_dict.get(action)
        method(value)

    def __save(self, value):
        self._cls.save(value)

    def __update(self, value):
        chain_id = value.get('chain_id', None)
        seq = value.get('seq', None)
        assert chain_id is not None and seq is not None
        if self.__exist(chain_id, seq):
            self._cls.update(chain_id, seq, value)
        else:
            value['_action'] = 'update'
            msg_queue.put(value)

    def __exist(self, chain_id, seq):
        return self._cls.exist(chain_id, seq)

    def __del__(self):
        pass
        # while msg_queue.qsize() > 0:
        #     time.sleep(0.5)
        # self.__receive_msg(exist_when_empty=True)
        # global __manager_status
        # __manager_status = False


class Tracker(object):
    def __init__(self, chain_id=None, chain_name=None):
        """ begin to track
        :param chain_name: name of method calling chain
        :return:
        """
        self.__seq = -1
        self.chain_id = chain_id or uuid.uuid4().get_hex()
        self.chain_name = chain_name or self.chain_id
        self.last_message = None
        global _manager
        assert _manager, "TrackerManager must init before Tracker!"
        assert isinstance(_manager, BaseAdaptor)
        self.store = _manager
        self.total_took = 0
        self.first_timestamp = self._curr_time
        self.tracking(depth=7)

    @property
    def _seq_next(self):
        self.__seq += 1
        return self.__seq

    @property
    def _seq_curr(self):
        return self.__seq

    @property
    def _curr_time(self):
        return int(time.time() * 1000)

    def tracking(self, desc=None, exception=None, return_value=None, depth=3):
        """ track the calling chain list
        :param desc: description message of what you are tracking
        :param exception: when catch the exception you can pass it to track
        :param return_value: method return value you want to monitor
        :return:
        """
        self.__send(desc, exception, return_value, depth=depth)

    def __send_update(self, seq=0, data_dict=None):
        if not data_dict:
            return
        msg = dict(
                chain_id=self.chain_id,
                seq=seq,
                _action='update'
        )
        msg.update(data_dict)
        msg_queue.put(msg)

    def __send(self, desc=None, exception=None, return_value=None, track_finished=False, depth=3):
        exc_message = None
        exc_info = None
        end_timestamp = self._curr_time
        if exception:
            assert isinstance(exception, Exception)
            exc_message = exception.message.message
            exc_info = traceback.format_exc()

        if track_finished:
            info = self.__get_caller_info(depth)
            print info
        else:
            info = self.__get_caller_info(depth)
            print info
        msg = {
            'chain_id': self.chain_id,
            'seq': self._seq_next,
            'chain_name': self.chain_name,
            'took': 0,
            'return_value': return_value,
            'bgn_timestamp': self._curr_time,
            'end_timestamp': end_timestamp,
            'desc': desc,
            'exception_message': exc_message,
            'exception_stack': exc_info,
            'track_finished': track_finished,
            'caller_filename': info[0],
            'caller_lineno': info[1],
            'caller_function_name': info[2],
            'caller_line': info[3]
        }

        if self.last_message:  # has last message
            msg, self.last_message = self.last_message, msg
            msg['end_timestamp'] = end_timestamp
            msg['took'] = end_timestamp - msg['bgn_timestamp']

            self._catch_finish_or_exception(msg, exception, track_finished, end_timestamp)
            msg_queue.put(msg)
            logger.debug("tracker took %d put message in queue %s", self.total_took, json.dumps(msg))
        elif self._seq_curr == 0:  # generally message as seq 0
            msg_queue.put(msg)
        else:
            self._catch_finish_or_exception(msg, exception, track_finished, end_timestamp)
            self.last_message = msg

    def _catch_finish_or_exception(self, msg, exception=None, track_finished=False, end_timestamp=None):
        if exception:
            assert isinstance(exception, Exception)
            exc_message = exception.message.message
            exc_info = traceback.format_exc()
            self.__send_update(0, dict(exception_message=exc_message, exception_stack=exc_info))
            msg['exception_message'] = exc_message
            msg['exception_stack'] = exc_info

        if track_finished:
            self.total_took = end_timestamp - self.first_timestamp
            msg['track_finished'] = True
            self.__send_update(0, dict(
                    end_timestamp=end_timestamp,
                    took=self.total_took,
                    track_finished=True
            ))

    def __get_caller_info(self, depth=3):
        """
        :param depth: frame depth number
        :return: filename, line_number, function_name, lines, index
        """
        ret = inspect.getouterframes(inspect.currentframe())[depth]
        return ret[1:]

    def __del__(self):
        """
        track finish
        :return:
        """
        self.__send(track_finished=True, depth=6)
        pass
