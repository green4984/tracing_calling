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
import abc
import threading

__manager_status = False
_manager = None

def track(func):
    functools.wraps(func)

    def _wrapper(*args, **kwargs):
        setattr(func, '__track__', True)
        result = func(*args, **kwargs)
        delattr(func, '__track__')
        return result

    return _wrapper


class BaseAdaptor(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self):
        pass

    @abc.abstractmethod
    def save(self, value):
        pass

    @abc.abstractmethod
    def update(self, chain_id, seq, key, value):
        pass

    def serialize(self, data):
        return json.dumps(data)

    def deserialize(self, data):
        return json.loads(data)


class RedisAdaptor(BaseAdaptor):
    def __init__(self, redis_uri):
        import redis
        self.__redis = redis.from_url(redis_uri)
        super(RedisAdaptor, self).__init__()

    def save(self, value):
        assert value
        assert isinstance(value, dict)
        key = value.get('chain_id')
        self.__redis.lpush(key, json.dumps(value))

    def update(self, chain_id, seq, key, value):
        if not value:
            return
        old_value = self.__redis.lrange(chain_id, 0, 0)
        if old_value and len(old_value) > 0:
            old_value = old_value[0]
            old_value = self.deserialize(old_value)
            assert isinstance(old_value, dict)
            old_value[key] = value
            print old_value
            self.__redis.lset(chain_id, seq, self.serialize(old_value))


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

    def __init_send_thread(self):
        t = threading.Thread(target=self.__save)
        t.setDaemon(True)
        t.start()

    def __save(self):
        global __manager_status
        value = None
        while True:
            try:
                if not __manager_status:
                    logger.warning("exit send thread!!")
                    return
                value = msg_queue.get(timeout=10)
                logger.debug("get data from msg_queue %s", value)
                self._cls.save(value)
            except Queue.Empty as e:
                logger.debug("get data from msg_queue empty %s", e.message, exc_info=1)

    def update(self, chain_id, seq, key, value):
        self._cls.update(chain_id, seq, key, value)

    def get(self, chain_id, seq, key):
        return self._cls.lrange(chain_id, 0, 0)

    def __del__(self):
        global __manager_status
        __manager_status = False


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
        global _manager
        assert _manager, "TrackerManager must init before Tracker!"
        assert isinstance(_manager, BaseAdaptor)
        self.store = _manager
        self.tracking()

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
            self.store.update(self.chain_id, 0, 'exception_message', exc_message)
        timestamp = int(time.time() * 1000)
        info = self.__get_caller_info(3)
        message_formater = {
            'chain_id': self.chain_id,
            'seq': self._seq,
            'chain_name': self.chain_name,
            'took': 0,
            'return_value': return_value,
            'bgn_timestamp': timestamp,
            'end_timestamp': timestamp,
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
            message_formater, self.last_message = self.last_message, message_formater

            message_formater['end_timestamp'] = int(time.time() * 1000)
            message_formater['took'] = message_formater['end_timestamp'] - message_formater['bgn_timestamp']
            if track_finished:
                message_formater['track_finished'] = True
                self.store.update(self.chain_id, 0, 'end_timestamp', message_formater['end_timestamp'])
            logger.debug("tracker put message in queue %s", json.dumps(message_formater))
            msg_queue.put(message_formater)
        else:
            self.last_message = message_formater

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
        self.__send(track_finished=True)
        pass
