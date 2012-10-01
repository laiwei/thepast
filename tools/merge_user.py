import sys
sys.path.append('../')

from past.store import db_conn

def merge_a2b(del_uid, merged_uid):
    
    
    print "-------update status:%s 2 %s" % (del_uid, merged_uid)
    db_conn.execute("update status set user_id=%s where user_id=%s", (merged_uid, del_uid))

    print "-------update alias:%s 2 %s" % (del_uid, merged_uid)
    db_conn.execute("update user_alias set user_id=%s where user_id=%s", (merged_uid, del_uid))
    
    print "-------update synctask:%s 2 %s" % (del_uid, merged_uid)
    db_conn.execute("update sync_task set user_id=%s where user_id=%s", (merged_uid, del_uid))

    db_conn.commit()

