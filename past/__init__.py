#-*- coding:utf-8 -*-

from flask import Flask 

#-- create app --
app = Flask(__name__)
app.config.from_object("past.config")

##-- register blueprint --
from past.connect import blue_print as connect_bp
from past.dev import blue_print as dev_bp
from past.weixin import blue_print as weixin_bp
app.register_blueprint(connect_bp, url_prefix="/connect")
app.register_blueprint(dev_bp, url_prefix="/dev")
app.register_blueprint(weixin_bp, url_prefix="/weixin")

import view

from utils import filters
from utils import wrap_long_line
from utils import markdownize

app.jinja_env.filters['nl2br'] = filters.nl2br
app.jinja_env.filters['linkify'] = filters.linkify
app.jinja_env.filters['html_parse'] = filters.html_parse
app.jinja_env.filters['wrap_long_line'] = wrap_long_line
app.jinja_env.filters['markdownize'] = markdownize
app.jinja_env.filters['isstr'] = lambda x: isinstance(x, basestring)
app.jinja_env.filters['stream_time'] = filters.stream_time
