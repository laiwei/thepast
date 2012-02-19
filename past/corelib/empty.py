# encoding: utf-8
"""
empty.py
from douban code, cool
"""

class Empty(object):
    def __call__(self, *a, **kw):
        return empty
    def __nonzero__(self):
        return False
    def __contains__(self, item):
        return False
    def __repr__(self):
        return '<Empty Object>'
    def __str__(self):
        return ''
    def __eq__(self, v):
        return isinstance(v, Empty)
    def __getattr__(self, name):
        if not name.startswith('__'):
            return empty
        raise AttributeError(name)
    def __len__(self):
        return 0
    def __getitem__(self, key):
        return empty
    def __setitem__(self, key, value):
        pass
    def __delitem__(self, key):
        pass
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration

empty = Empty()
