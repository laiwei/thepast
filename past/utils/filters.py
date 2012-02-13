#!-*- coding:utf8 -*-
import re

from past.utils import escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n)')

def nl2br(value):
    result = u"<br/>\n".join(_paragraph_re.split(value))
    return result

def linkify(text):
    return escape.linkify(text)

def html_parse(s, preserve):
    return escape.MyHTMLParser.parse(text, preserve)

