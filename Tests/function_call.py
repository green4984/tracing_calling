# -*- coding: utf-8 -*-

import sys
import time

TIME_CALL = {}

class FunctionCall(object):
    pass

def trace_calls_and_returns(frame, event, arg):
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    filename = co.co_filename
    key = "%s:%s" % (filename, func_name)
    if key not in TIME_CALL:
        return
    line_no = frame.f_lineno
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    caller_func_name = caller.f_code.co_name
    if event == 'call':
        TIME_CALL[key] = time.time()
        print '%s call %s on line %s of %s at time %f' % (caller_func_name, func_name, caller_line_no, filename, time.time())
        return trace_calls_and_returns
    elif event == 'return':
        bgn_time = TIME_CALL[key]
        print '%s return at time %f spend time %f' % (func_name, time.time(), time.time() - bgn_time)
    return

def register_tracker(func_list=None):
    import sys
    global TIME_CALL
    func_list = func_list or []
    for func in func_list:
        TIME_CALL.setdefault(func[0] + u':' + func[1], 0)
    sys.settrace(trace_calls_and_returns)

# def trace_lines(frame, event, arg):
#     if event != 'line':
#         return
#     co = frame.f_code
#     func_name = co.co_name
#     line_no = frame.f_lineno
#     filename = co.co_filename
#     print '  %s line %s' % (func_name, line_no)
#
# def trace_calls(frame, event, arg):
#     print event
#     if event != 'call':
#         return
#     co = frame.f_code
#     func_name = co.co_name
#     if func_name == 'write':
#         # Ignore write() calls from print statements
#         return
#     line_no = frame.f_lineno
#     filename = co.co_filename
#     print 'Call to %s on line %s of %s' % (func_name, line_no, filename)
#     if func_name in TRACE_INTO:
#         # Trace into this function
#         return trace_lines
#     return
#
# def c(input):
#     print 'input =', input
#     print 'Leaving c()'
#
# def b(arg):
#     val = arg * 5
#     c(val)
#     print 'Leaving b()'
#
# def a():
#     b(2)
#     print 'Leaving a()'
#
# TRACE_INTO = ['b']
#
# sys.settrace(trace_calls)
# a()

# def trace_calls(frame, event, arg):
#     if event != 'call':
#         return
#     co = frame.f_code
#     func_name = co.co_name
#     if func_name == 'write':
#         # Ignore write() calls from print statements
#         return
#     func_line_no = frame.f_lineno
#     func_filename = co.co_filename
#     caller = frame.f_back
#     caller_line_no = caller.f_lineno
#     caller_filename = caller.f_code.co_filename
#     print 'Call to %s on line %s of %s from line %s of %s' % \
#         (func_name, func_line_no, func_filename,
#          caller_line_no, caller_filename)
#     return
#
# def b():
#     print 'in b()'
#
# def a():
#     print 'in a()'
#     b()
#
# sys.settrace(trace_calls)
# a()
