import sys
sys.path.append('../')
import os
import commands

def file_visitor(args, dir_, files):
    if not isinstance(files, list):
        return
    for f in files:
        if not (f.startswith("thepast.me_") and f.endswith(".pdf")):
            continue
        cmd = "cd ../var/down/pdf/ && tar -zcvf %s.tar.gz %s && rm %s" %(f, f, f)
        print "-----", cmd
        print commands.getoutput(cmd)

os.path.walk("../var/down/pdf/", file_visitor, None)
