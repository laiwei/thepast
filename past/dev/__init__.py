#-*- coding:utf-8 -*-
# blueprint: dev

from flask import Blueprint
from flask import redirect, render_template, g, abort, flash, url_for

from past import config, consts

blue_print = Blueprint("dev", __name__, template_folder="templates", static_folder="static")

from .view import token 
from .view import api

@blue_print.before_request
def before_request():
    print "--- in dev blue_print"


