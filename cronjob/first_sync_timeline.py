#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

import os
import time
import datetime
import commands

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import past
import jobs
from past.model.status import TaskQueue, SyncTask, Status
from past import config

if __name__ == "__main__":

    try:
        queue_ids = TaskQueue.get_all_ids()
        print '%s queue length: %s' %(datetime.datetime.now(),len(queue_ids)) 
        for qid in queue_ids:
            queue = TaskQueue.get(qid)
            if queue and queue.task_kind == config.K_SYNCTASK:
                print 'syncing task id:', queue.task_id
                sync_task = SyncTask.get(queue.task_id)
                if not sync_task:
                    continue

                ## 现在不同步豆瓣日记
                if str(sync_task.category) == str(config.CATE_DOUBAN_NOTE):
                    continue

                ## 同步wordpress rss
                if str(sync_task.category) == str(config.CATE_WORDPRESS_POST):
                    jobs.sync_wordpress(sync_task)
                    queue.remove()
                    continue

                max_sync_times = 0
                min_id = Status.get_min_origin_id(sync_task.category, sync_task.user_id)
                if sync_task:
                    while True:
                        if max_sync_times >= 20:
                            break
                        r = jobs.sync(sync_task, old=True)
                        new_min_id = Status.get_min_origin_id(sync_task.category, sync_task.user_id)
                        if r == 0 or new_min_id == min_id:
                            break
                        min_id = new_min_id
                        max_sync_times += 1
            queue.remove()
            time.sleep(1)
        time.sleep(1)
    except Exception, e:
        print e
