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
    def update(self, chain_id, seq, data_dict=None):
        pass

    @abc.abstractmethod
    def exist(self, chain_id, seq):
        pass

    def get(self, chain_id, seq):
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
        self.__redis.rpush(key, self.serialize(value))

    def get(self, chain_id, seq):
        return self.__redis.lrange(chain_id, seq, seq)

    def exist(self, chain_id, seq):
        item = self.get(chain_id, seq)
        if item:
            return True
        return False

    def update(self, chain_id, seq, data_dict=None):
        if not data_dict:
            return
        old_value = self.get(chain_id, seq)
        if old_value and len(old_value) > 0:
            old_value = old_value[0]
            old_value = self.deserialize(old_value)
            assert isinstance(old_value, dict)
            for key, v in data_dict.iteritems():
                old_value[key] = v
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
        t = threading.Thread(target=self.__receive_msg)
        t.setDaemon(True)
        t.start()

    def __receive_msg(self):
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
                logger.debug("get data from msg_queue empty %s", e.message, exc_info=1)

    def __router(self, value):
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
        self.chain_name = chain_name or self.chain_id
        self.last_message = None
        global _manager
        assert _manager, "TrackerManager must init before Tracker!"
        assert isinstance(_manager, BaseAdaptor)
        self.store = _manager
        self.total_took = 0
        self.first_timestamp = self._curr_time
        self.tracking()

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

    def tracking(self, desc=None, exception=None, return_value=None):
        """ track the calling chain list
        :param desc: description message of what you are tracking
        :param exception: when catch the exception you can pass it to track
        :param return_value: method return value you want to monitor
        :return:
        """
        self.__send(desc, exception, return_value)

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

    def __send(self, desc=None, exception=None, return_value=None, track_finished=False):
        exc_message = None
        exc_info = None
        end_timestamp = self._curr_time
        # FIXME exception occur, need update seq-1 message
        if exception:
            assert isinstance(exception, Exception)
            exc_message = exception.message.message
            exc_info = traceback.format_exc()

        info = self.__get_caller_info(3)
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

            if exception:
                self.__send_update(0, dict(exception_message=exc_message))
                # last operation get exception, set this msg exception
                msg['exception_message'] = exc_message
                msg['exception_stack'] = exc_info

            if track_finished:
                self.total_took = end_timestamp - self.first_timestamp
                msg['track_finished'] = True
                self.__send_update(0, dict(
                    end_timestamp=end_timestamp,
                    took=self.total_took
                ))
            msg_queue.put(msg)
            logger.debug("tracker took %d put message in queue %s", self.total_took, json.dumps(msg))
        else:
            self.last_message = msg

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
