#-*- coding:utf-8 -*-

import datetime

YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = datetime.datetime.now().strftime("%Y-%m-%d")
TOMORROW = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")


YES = 'Y'
NO = 'N'

USER_PRIVACY_PRIVATE = 'X'
USER_PRIVACY_PUBLIC = 'P'

NOTE_FMT_PLAIN = 'P'
NOTE_FMT_MARKDOWN = 'M'
