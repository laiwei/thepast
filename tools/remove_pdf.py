import sys
sys.path.append('../')
import os

from past.store import db_conn

user_ids = []
cursor = db_conn.execute('''select user_id from pdf_settings''')
if cursor:
    rows = cursor.fetchall()
    user_ids = [row[0] for row in rows]
cursor and cursor.close()

print user_ids, len(user_ids)

def file_visitor(args, dir_, files):
    #print "-------", dir_, files
    pendding = set()
    if not isinstance(files, list):
        return
    for f in files:
        if not (f.startswith("thepast.me") and f.endswith(".pdf.tar.gz")):
            continue
        user_id = int(f.split("_")[1])
        if user_id not in user_ids:
            pendding.add(user_id)
    print pendding, len(pendding)
    for user_id in pendding:
        print '---deleting pdf of', user_id
        os.popen("rm ../var/down/pdf/thepast.me_%s_2*.pdf.tar.gz" %user_id)

os.path.walk("../var/down/pdf/", file_visitor, None)
