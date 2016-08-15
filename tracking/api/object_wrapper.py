# -*- coding: utf-8 -*-
import inspect
import sys

import six

from tracking.api.trace_wrapper import ExternalTraceWrapper


def resolve_path(module, name):
    """ get real module function by name
    :param module:
    :param name: handle name like like Session.request etc.
    :return:
    """
    if isinstance(module, six.string_types):
        __import__(module)
        module = sys.modules[module]

    parent = module
    path = name.split('.')
    attribute = path[0]
    original = getattr(parent, attribute)

    for attribute in path[1:]:
        parent = original
        if inspect.isclass(original):
            for cls in inspect.getmro(original):
                if attribute in vars(cls):
                    original = vars(cls)[attribute]
                    break
            else:
                original = getattr(original, attribute)
        else:
            original = getattr(original, attribute)
    return (parent, attribute, original)


def wrap_object(module, name, factory, *args, **kwargs):
    (parent, attribute, original) = resolve_path(module, name)
    wrapper = factory(original, *args, **kwargs)
    # apply patch
    setattr(parent, attribute, wrapper)

def wrap_external_trace(module, object_path, library, url):
    wrap_object(module, object_path, ExternalTraceWrapper, library, url)