#-*- coding:utf-8 -*-
# blueprint: dev -> view -> token

from past.dev import blue_print

from past.utils.logger import logging
log = logging.getLogger(__file__)

@blue_print.route("/token")
def token_index():
    return "ok"

