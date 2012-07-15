#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

from past.store import mc
from past.model.user import UserAlias, User
from past.model.status import SyncTask, TaskQueue
from past import config


def bind(uid, feed_uri):
    user = User.get(uid)
    if not user:
        print 'no user'
        return
    ua = UserAlias.bind_to_exists_user(user, 
            config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS], feed_uri)
    if not ua:
        print "no user alias"
    else:
        ##添加同步任务
        t = SyncTask.add(config.CATE_WORDPRESS_POST, user.id)
        t and TaskQueue.add(t.id, t.kind)
        ##删除confiration记录
        mc.delete("wordpress_bind:%s" %user.id)

if __name__ == "__main__":
    print sys.argv
    if len(sys.argv) == 3:
        bind(sys.argv[1], sys.argv[2])
    else:
        print "bind uid feed"
        
