#-*- coding:utf-8 -*-

'''from douban code, cool '''

import inspect
from functools import wraps
import time

try:
    import cPickle as pickle
except:
    import pickle

from .empty import Empty
from .format import format

from past.store import mc

# some time consts for mc expire
HALF_HOUR =  1800
ONE_HOUR = 3600
HALF_DAY = ONE_HOUR * 12
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_DAY * 7
ONE_MONTH = ONE_DAY * 30


def gen_key(key_pattern, arg_names, defaults, *a, **kw):
    return gen_key_factory(key_pattern, arg_names, defaults)(*a, **kw)


def gen_key_factory(key_pattern, arg_names, defaults):
    args = dict(zip(arg_names[-len(defaults):], defaults)) if defaults else {}
    if callable(key_pattern):
        names = inspect.getargspec(key_pattern)[0]
    def gen_key(*a, **kw):
        aa = args.copy()
        aa.update(zip(arg_names, a))
        aa.update(kw)
        if callable(key_pattern):
            key = key_pattern(*[aa[n] for n in names])
        else:
            key = format(key_pattern, *[aa[n] for n in arg_names], **aa)
        return key and key.replace(' ','_'), aa
    return gen_key

def cache_(key_pattern, mc, expire=0, max_retry=0):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            if not key:
                return f(*a, **kw)
            if isinstance(key, unicode):
                key = key.encode("utf8")
            r = mc.get(key)

            # anti miss-storm
            retry = max_retry
            while r is None and retry > 0:
                time.sleep(0.1)
                r = mc.get(key)
                retry -= 1
            r = pickle.loads(r) if r else None
            
            if r is None:
                r = f(*a, **kw)
                if r is not None:
                    mc.set(key, pickle.dumps(r), expire)
            
            if isinstance(r, Empty):
                r = None
            return r
        _.original_function = f
        return _
    return deco

def pcache_(key_pattern, mc, count=300, expire=0, max_retry=0):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        if not ('limit' in arg_names):
            raise Exception("function must has 'limit' in args")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            start = args.pop('start', 0)
            limit = args.pop('limit')
            start = int(start)
            limit = int(limit)
            if not key or limit is None or start+limit > count:
                return f(*a, **kw)
            if isinstance(key, unicode):
                key = key.encode("utf8")
            r = mc.get(key)
            
            # anti miss-storm
            retry = max_retry
            while r is None and retry > 0:
                time.sleep(0.1)
                r = mc.get(key)
                retry -= 1
            r = pickle.loads(r) if r else None

            if r is None:
                r = f(limit=count, **args)
                mc.set(key, pickle.dumps(r), expire)
            return r[start:start+limit]

        _.original_function = f
        return _
    return deco

def delete_cache_(key_pattern, mc):
    def deco(f):
        arg_names, varargs, varkw, defaults = inspect.getargspec(f)
        if varargs or varkw:
            raise Exception("do not support varargs")
        gen_key = gen_key_factory(key_pattern, arg_names, defaults)
        @wraps(f)
        def _(*a, **kw):
            key, args = gen_key(*a, **kw)
            r = f(*a, **kw)
            mc.delete(key)
            return r
        return _
        _.original_function = f
    return deco

def create_decorators(mc):

    def _cache(key_pattern, expire=0, mc=mc, max_retry=0):
        return cache_(key_pattern, mc, expire=expire, max_retry=max_retry)
    
    def _pcache(key_pattern, count=300, expire=0, max_retry=0):
        return pcache_(key_pattern, mc, count=count, expire=expire, max_retry=max_retry)
    
    def _delete_cache(key_pattern):
        return delete_cache_(key_pattern, mc=mc)
    
    return dict(cache=_cache, pcache=_pcache, delete_cache=_delete_cache)
                
    
globals().update(create_decorators(mc))

