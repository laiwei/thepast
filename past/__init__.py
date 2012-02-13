#-*- coding:utf-8 -*-

from flask import Flask 

#-- create app --
app = Flask(__name__)
app.config.from_object("past.config")

import views
from utils import filters

app.jinja_env.filters['nl2br'] = filters.nl2br
app.jinja_env.filters['linkify'] = filters.linkify
app.jinja_env.filters['html_parse'] = filters.html_parse
