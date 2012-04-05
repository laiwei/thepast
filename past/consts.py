#-*- coding:utf-8 -*-

import datetime

YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
TOMORROW = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
