#-*- coding:utf-8 -*-

import sys
sys.path.append("../")

import time
import datetime
import calendar
import commands

activate_this = '../env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from past.utils.pdf import generate_pdf, get_pdf_filename, is_pdf_file_exists, get_pdf_full_filename
from past.model.user import User, UserAlias, PdfSettings
from past.model.status import Status
from past import config


def generate(user_id, date, order='asc'):
    try:
        uas = UserAlias.gets_by_user_id(user_id)
        if not uas:
            return

        start_date = datetime.datetime(date.year, date.month, 1)
        end_date = datetime.datetime(date.year, date.month,
                calendar.monthrange(date.year, date.month)[1], 23, 59, 59)

        pdf_filename = get_pdf_filename(user_id, date.strftime("%Y%m"), "")
        pdf_filename_compressed = get_pdf_filename(user_id, date.strftime("%Y%m"))
        print '----generate pdf:', start_date, ' to ', end_date, ' file is', pdf_filename

        if is_pdf_file_exists(pdf_filename_compressed):
            print '---- %s exists, so ignore...' % pdf_filename_compressed
            return

        status_ids = Status.get_ids_by_date(user_id, start_date, end_date)[:900]
        if order == 'asc':
            status_ids = status_ids[::-1]
        if not status_ids:
            print '----- status ids is none', status_ids
            return
        generate_pdf(pdf_filename, user_id, status_ids)

        if not is_pdf_file_exists(pdf_filename):
            print '----%s generate pdf for user:%s fail' % (datetime.datetime.now(), user_id)
        else:
            commands.getoutput("cd %s && tar -zcf %s %s && rm %s" %(config.PDF_FILE_DOWNLOAD_DIR, 
                    pdf_filename_compressed, pdf_filename, pdf_filename))
            print '----%s generate pdf for user:%s succ' % (datetime.datetime.now(), user_id)
    except Exception, e:
        import traceback
        print '%s %s' % (datetime.datetime.now(), traceback.format_exc())

def generate_pdf_by_user(user_id):
    user = User.get(user_id)
    if not user:
        return

    #XXX:暂时只生成2012年的(uid从98开始的用户)
    #XXX:暂时只生成2012年3月份的(uid从166开始的用户)
    start_date = Status.get_oldest_create_time(None, user_id)
    if not start_date:
        return
    now = datetime.datetime.now()
    now = datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days = calendar.monthrange(now.year, now.month)[1])

    d = start_date
    while d <= now:
        generate(user_id, d)

        days = calendar.monthrange(d.year, d.month)[1]
        d += datetime.timedelta(days=days)
        d = datetime.datetime(d.year, d.month, 1)


if __name__ == "__main__":
    for uid in PdfSettings.get_all_user_ids():
        #print '------begin generate pdf of user:', uid
        #generate_pdf_by_user(uid)

        now = datetime.datetime.now()
        last_mongth = datetime.datetime(now.year, now.month, now.day) \
                - datetime.timedelta(days = calendar.monthrange(now.year, now.month)[1])
        print '----- generate last month pdf of user:', last_mongth, uid
        generate(uid, last_mongth)
