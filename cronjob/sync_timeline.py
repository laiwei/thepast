#-*- coding:utf-8 -*-

import os
import time
import commands

activate_this = '%s/env/bin/activate_this.py' % os.path.dirname(os.path.abspath(__file__))
execfile(activate_this, dict(__file__=activate_this))

if __name__ == "__main__":
    while True: 

        print commands.getoutput("python jobs.py -t old -c 101 -n 1")
        print commands.getoutput("python jobs.py -t old -c 102 -n 1")
        print commands.getoutput("python jobs.py -t old -c 200 -n 1")
        print commands.getoutput("python jobs.py -t old -c 400 -n 1")
        print commands.getoutput("python jobs.py -t new -c 101 -n 1")
        print commands.getoutput("python jobs.py -t new -c 102 -n 1")
        print commands.getoutput("python jobs.py -t new -c 200 -n 1")
        print commands.getoutput("python jobs.py -t new -c 400 -n 1")
