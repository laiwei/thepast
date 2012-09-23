#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import datetime
from past import config
from past.model.status import SyncTask
from past.model.user import User
import jobs

if __name__ == '__main__':
    user = User.get(sys.argv[1])
    old = sys.argv[2] == "old"

    if not user:
        print "no such user"
        exit(1)

    ts = SyncTask.gets_by_user(user)
    if not ts:
        print "no sync tasks"

    for t in ts:
        try:
            if t.category == config.CATE_WORDPRESS_POST:
                jobs.sync_wordpress(t)
            else:
                jobs.sync(t, old=old)
        except Exception, e:
            import traceback
            print "%s %s" % (datetime.datetime.now(), traceback.format_exc())

        

