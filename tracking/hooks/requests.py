# -*- coding: utf-8 -*-


from ..api.object_wrapper import wrap_external_trace

def tracking_hook_request_api(module):
    def url(method, url, *args, **kwargs):
        return url

    if hasattr(module, 'request'):
        # wrap external trace
        wrap_external_trace(module, 'request', 'requests', url)
