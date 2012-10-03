#-*- coding:utf-8 -*-
# blueprint: connect

from flask import Blueprint
from flask import redirect, render_template, g, abort, flash, url_for

from past import config, consts

blue_print = Blueprint("connect", __name__, template_folder="templates", static_folder="static")

import view

@blue_print.before_request
def before_request():
    print "--- in connect blue_print"


