#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

import time
import datetime

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from past.utils.pdf import generate_pdf, get_pdf_filename, is_pdf_file_exists
from past.model.user import User

if __name__ == "__main__":
    
    for uid in User.get_ids(0, 10000000):
        try:
            pdf_filename = get_pdf_filename(uid)
            print pdf_filename
            generate_pdf(pdf_filename, uid, 0, 1000, capacity=-1)
            if not is_pdf_file_exists(pdf_filename):
                print '%s generate pdf for user:%s fail' % (datetime.datetime.now(), uid)
            else:
                print '%s generate pdf for user:%s succ' % (datetime.datetime.now(), uid)
        except Exception, e:
            import traceback
            print '%s %s' % (datetime.datetime.now(), traceback.format_exc())

        time.sleep(1)
