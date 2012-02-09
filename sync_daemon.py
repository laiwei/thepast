#-*- coding:utf-8 -*-

import os
import time

activate_this = '%s/env/bin/activate_this.py' % os.path.dirname(os.path.abspath(__file__))
execfile(activate_this, dict(__file__=activate_this))

if __name__ == "__main__":
    
    python jobs.py -t old -c 100 -n 1
    python jobs.py -t old -c 101 -n 1
    python jobs.py -t old -c 200 -n 1
    python jobs.py -t old -c 400 -n 1
    python jobs.py -t new -c 100 -n 1
    python jobs.py -t new -c 101 -n 1
    python jobs.py -t new -c 200 -n 1
    python jobs.py -t new -c 400 -n 1

    time.sleep(60*10)

