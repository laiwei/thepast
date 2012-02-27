#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

import os
import time
import commands

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

if __name__ == "__main__":

    #print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t old -c 101 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t old -c 102 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t old -c 200 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t old -c 400 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t old -c 500 -n 1")
    #print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t new -c 101 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t new -c 102 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t new -c 200 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t new -c 400 -n 1")
    print commands.getoutput("../env/bin/python /home/work/proj/thepast/jobs.py -t new -c 500 -n 1")

