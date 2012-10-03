#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

import os
import time
import commands

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

if __name__ == "__main__":
    for c in [100, 200, 300, 400, 500, 700, 702, 703, 704, 800,]:
        for t in ['old', 'new']:
            print commands.getoutput("../env/bin/python ../jobs.py -t %s -c %s -n 1" %(t, c))
