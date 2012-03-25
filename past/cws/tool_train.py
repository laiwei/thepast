#-*- coding:utf-8 -*-

from collections import defaultdict

from past.model.status import get_all_text_by_user

def generate_docs_file(file_):
    from past.model.user import User
    uids = User.get_ids(start=0, limit=400)
    with open(file_, "aw") as f:
        for x in uids:
            print 'get user %s text' % x
            text = get_all_text_by_user(x)
            f.write(text.encode("utf8"))



def generate_term_frq():
    infile = "./cuted_past_dict.txt"
    dict_ = defaultdict(int)
    with open(infile, 'r') as f:
        for line in f:
            l = line.split(" ")
            for x in l:
                dict_[x] += 1

    
    kws = sorted(dict_.items(), key=lambda x:x[1], reverse=True) 

    ofile = "./past.frq.txt"
    with open(ofile, 'w') as f:
        for k,v in kws:
            f.write("%s %s\n" %(k,v))
            f.flush()

generate_term_frq()
