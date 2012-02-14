#-*- coding:utf-8 -*-

import sys
sys.path.append('../')

import past
from past import config
from past.model.user import UserAlias
from past.model.status import SyncTask

all_alias_ids = UserAlias.get_ids()
for id_ in all_alias_ids:
    print id_
    ua = UserAlias.get_by_id(id_)
    if not ua:
        continue
    print ua

    if ua.type == 'D':
        SyncTask.add(config.CATE_DOUBAN_NOTE, ua.user_id)
        SyncTask.add(config.CATE_DOUBAN_MINIBLOG, ua.user_id)

    if ua.type == 'S':
        SyncTask.add(config.CATE_SINA_STATUS, ua.user_id)

    if ua.type == 'T':
        SyncTask.add(config.CATE_TWITTER_STATUS, ua.user_id)

