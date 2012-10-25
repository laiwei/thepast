#-*- coding:utf-8 -*-
# blueprint: dev -> view -> api

from past.dev import blue_print

from past.utils.logger import logging
log = logging.getLogger(__file__)

@blue_print.route("/api")
def api_index():
    return "ok"

