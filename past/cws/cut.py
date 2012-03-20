#-*- coding:utf-8 -*-

import re
import os
import commands
from collections import defaultdict

from past import config
from past.corelib.cache import cache

""" 
判断unicode码是否为中文字符. 
""" 
def is_cn_char(i): 
    return 0x4e00<=ord(i)<0x9fa6 

def is_cn_or_en(i): 
    o = ord(i) 
    return o<128 or 0x4e00<=o<0x9fa6 

def get_terms_tf(text, sep=" ", max_items=5000):
    r = text.split(sep)
    d = defaultdict(int)
    for word in r:
        d[word] += 1
    
    sorted_by_tf = sorted(d.items(), key=lambda x:x[1], reverse=True) 
    return sorted_by_tf[:max_items]

def terms_sort_by_idf(term_list):
    df_dict = load_dict()
    kw = {}
    for term, frq in term_list:
        ## 未登录词的doc-frequency默认为1
        df = df_dict.get(term, 1)
        print '++++++:',term, df
        kw[term] = frq / float(df)

    sorted_kw = sorted(kw.items(), key=lambda x:x[1], reverse=True)
    return sorted_kw

@cache("chinese_dict_with_frequency")
def load_dict():
    d = {}
    file_ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            config.CHINESE_DICT_WITH_FREQUENCY)

    with open(file_, 'r') as f:
        for line in f:
            term, frq = line.strip().split(" ")
            d[term] = frq
    return d

def get_keywords(user_id=config.MY_USER_ID):
    from past.model.status import Status
    text = ""
    status_ids = Status.get_ids(user_id, limit=10000)
    for s in Status.gets(status_ids):
        try:
            _t = ''.join( [x for x in s.text if is_cn_or_en(x)] )

            retweeted_data = s.get_retweeted_data()
            if retweeted_data:
                if isinstance(retweeted_data, basestring):
                    _t += retweeted_data
                else:
                    _t += retweeted_data.get_content()
            text += _t.replace('"', '').replace("`", "")
        except:
            pass
    print text
    cmd = '%s -t50 -N -a n -d %s -c utf8 -i "%s"|grep -E "^[0-9]+"' \
            % (config.SCWS, config.SCWS_XDB_DICT, text)
    cmd = cmd.encode("utf8")
    r = commands.getoutput(cmd)

    tf_list = []
    for line in r.split("\n"):
        lines = re.split("\s+", line)
        term = lines[1]
        frq = float(lines[3].split("(")[0])
        tf_list.append((term, frq))

    sorted_kw = terms_sort_by_idf(tf_list)
    for x in sorted_kw[:100]:
        print "--",x[0],x[1]

def cut_str(text):
    text = text.replace('"', '').replace("`", "")
    cmd = '%s -N -d %s -c utf8 -i "%s"' \
            % (config.SCWS, config.SCWS_XDB_DICT, text)
    print cmd
    r = commands.getoutput(cmd)
    return r

def generate_term_frq(file_):
    term_frq_dict = defaultdict(int)

    with open(file_, 'r') as f:
        for line in f:
            terms = cut_str(line)
            if terms:
                terms = terms.split(" ")
                for term in terms:
                    term_frq_dict[term] = term_frq_dict[term]+1

    return term_frq_dict
            
