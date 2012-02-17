#-*- coding:utf-8 -*-

import os
import time
import datetime
import commands

activate_this = '%s/env/bin/activate_this.py' % os.path.dirname(os.path.abspath(__file__))
execfile(activate_this, dict(__file__=activate_this))

import past
import jobs
from past.model.status import TaskQueue, SyncTask, Status
from past import config

if __name__ == "__main__":
    while True: 

        try:
            queue_ids = TaskQueue.get_all_ids()
            print '%s queue length: %s' %(datetime.datetime.now(),len(queue_ids)) 
            for qid in queue_ids:
                queue = TaskQueue.get(qid)
                if queue and queue.task_kind == config.K_SYNCTASK:
                    print 'syncing task id:', queue.task_id
                    sync_task = SyncTask.get(queue.task_id)
                    max_sync_times = 0
                    min_id = Status.get_min_origin_id(sync_task.category, sync_task.user_id)
                    if sync_task:
                        while True:
                            if max_sync_times >= 3:
                                break
                            r = jobs.sync(sync_task, old=True)
                            new_min_id = Status.get_min_origin_id(sync_task.category, sync_task.user_id)
                            if r == 0 or new_min_id == min_id:
                                break
                            min_id = new_min_id
                            max_sync_times += 1
                queue.remove()
                time.sleep(5)
            time.sleep(30)
        except Exception, e:
            print '----except: %s' %e
            time.sleep(5)

        #print commands.getoutput("python jobs.py -t old -c 101 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 102 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 200 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 400 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 101 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 102 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 200 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 400 -n 1")
