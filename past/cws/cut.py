#-*- coding:utf-8 -*-

import re
import os
import commands
from collections import defaultdict

from past import config
from past.corelib.cache import cache
from past.utils import randbytes
from past.model.status import get_all_text_by_user

""" 
判断unicode码是否为中文字符. 
""" 
def is_cn_char(i): 
    return 0x4e00<=ord(i)<0x9fa6 

def is_cn_or_en(i): 
    o = ord(i) 
    return o<128 or 0x4e00<=o<0x9fa6 

@cache("hot_terms_dict")
def load_hot_terms():
    d = {}
    file_ = config.HOT_TERMS_DICT

    with open(file_, 'r') as f:
        for line in f:
            rs = line.strip().split(" ")
            term, frq = rs[0], rs[1]
            if term.isalpha():
                term = term.lower()
            d[term] = frq
    return d
    
def cut_str(text):
    text = text.replace('"', '').replace("`", "")
    cmd = '%s -N -d %s -c utf8 -i "%s"' \
            % (config.SCWS, config.SCWS_XDB_DICT, text)
    r = commands.getoutput(cmd)
    return r

@cache("user_keywords:{user_id}:{count}", 3600*6)
def get_keywords(user_id=config.MY_USER_ID, count=30):
    text = get_all_text_by_user(user_id)
    file_ = "/tmp/tag_%s" % randbytes(8)
    with open(file_, 'w') as f:
        f.write(text.encode("utf8"))
    try:
        cmd = '%s -I -d %s -c utf8 -t500 -i "%s"|grep -E "^[0-9]+"' \
                % (config.SCWS, config.HOT_TERMS_DICT, file_)
        r = commands.getoutput(cmd)
    except Exception, e:
        print e
    finally:
        os.path.exists(file_) and os.remove(file_)

    if not r:
        print '-----no keywords'
        return None
    
    term_frq = defaultdict(int)
    hot_keywords = load_hot_terms()
    for line in r.split("\n"):
        try:
            lines = re.split("\s+", line)
            term = lines[1]
            if term.isalpha():
                term = term.lower()
            if term in hot_keywords and term not in term_frq:
                frq = re.sub(r'\(.*\)', '', lines[3])
                term_frq[term] += float(frq)
        except Exception, e:
            print e
    tf_list = sorted(term_frq.items(), key=lambda x:x[1], reverse=True) 
    return tf_list[:count]
