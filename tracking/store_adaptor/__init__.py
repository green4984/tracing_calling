# -*- coding: utf-8 -*-
import abc
import json
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

    @abc.abstractmethod
    def status(self):
        pass

    def get(self, chain_id, seq):
        pass

    def serialize(self, data):
        return json.dumps(data)

    def deserialize(self, data):
        return json.loads(data)

