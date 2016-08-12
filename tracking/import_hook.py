# -*- coding: utf-8 -*-

import sys
import imp
import logging

logger = logging.getLogger(__name__)
_import_hooks = {}


def register_import_hook(name, callback):
    imp.acquire_lock()
    try:
        if not name or not callback:
            return

        if name not in _import_hooks or _import_hooks.get(name, None) is None:
            module = sys.modules.get(name, None)
            if module:
                # already import, run this callback immediately
                _import_hooks[name] = None
                callback(module)
                logger.debug("replace module %s!", name)
            else:
                _import_hooks[name] = [callback]
        else:
            # module has not been import, save it
            _import_hooks[name].append(callback)
    except Exception as e:
        logger.error(e.message, exc_info=1)
    finally:
        imp.release_lock()


def module_import_hook(module_name, function_name):
    def _callback(real_module):
        if not hasattr(real_module, '_hook_module_import'):
            setattr(real_module, '_hook_module_import', set())
        module_import = getattr(real_module, '_hook_module_import')
        if (module_name, function_name) in module_import:
            return

        module_import.add((module_name, function_name))
        hook_module = import_module(module_name)
        func = getattr(hook_module, function_name, None)
        if func:
            func(real_module)
        else:
            logger.debug("_module_import_hook error function_name '%s' not exist", function_name)

    return _callback


class _ImportHookLoader(object):
    def load_module(self, fullname):
        module = sys.modules[fullname]
        hooks = _import_hooks.get(fullname, [])
        if hooks:
            _import_hooks[fullname] = None
        for callback in hooks:
            callback(module)
        return module


class ImportHookFinder(object):
    def __init__(self):
        self._skip = {}

    def find_module(self, fullname, path=None):
        # sys.meta_path will use this function before find module in sys.path

        # we don't care this fullname if it is not in _import_hooks
        if not fullname in _import_hooks:
            return None

        # skip infinite loop
        if fullname in self._skip:
            return None
        try:
            self._skip.setdefault(fullname, None)
            __import__(fullname)
            return _ImportHookLoader()
        finally:
            del self._skip[fullname]


def import_module(module):
    __import__(module)
    return sys.modules[module]
