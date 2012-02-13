#-*- coding:utf-8 -*-

import os
import time
import commands

activate_this = '%s/env/bin/activate_this.py' % os.path.dirname(os.path.abspath(__file__))
execfile(activate_this, dict(__file__=activate_this))

import past
import jobs
from past.model.status import TaskQueue, SyncTask
from past import config

if __name__ == "__main__":
    while True: 

        queue_ids = TaskQueue.get_all_ids()
        print 'queue length:', len(queue_ids) 
        for qid in queue_ids:
            queue = TaskQueue.get(qid)
            if queue and queue.task_kind == config.K_SYNCTASK:
                print 'syncing task id:', queue.task_id
                sync_task = SyncTask.get(queue.task_id)
                if sync_task:
                    while True:
                        r = job.sync(t, old=True)
                        if r == 0:
                            break
            time.sleep(1)
        time.sleep(30)

        #print commands.getoutput("python jobs.py -t old -c 101 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 102 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 200 -n 1")
        #print commands.getoutput("python jobs.py -t old -c 400 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 101 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 102 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 200 -n 1")
        #print commands.getoutput("python jobs.py -t new -c 400 -n 1")
