# -*- coding: utf-8 -*-
from ..store_adaptor import BaseAdaptor
import logging

logger = logging.getLogger(__name__)


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

    def status(self):
        try:
            self.__redis.info()
            return True
        except Exception as e:
            logger.error(e.message, exc_info=1)
            return False
