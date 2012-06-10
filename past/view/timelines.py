#-*- coding:utf-8 -*-
import os
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

from flask import g, request, redirect, url_for, abort, render_template,\
        make_response, flash

from past import app
from past import config
from past.model.user import User
from past.model.status import Status

from past.utils import sizeof_fmt
from past.utils.pdf import is_pdf_file_exists, get_pdf_filename, get_pdf_full_filename
from past.utils.escape import json_encode
from past.cws.cut import get_keywords
from past import consts
from .utils import require_login, can_access_user

@app.route("/visual")
@require_login()
def myvisual():
    return redirect("/user/%s/visual" % g.user.id)

@app.route("/user/<uid>/visual")
@require_login()
def visual(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    if uid != g.user.id and u.get_profile_item('user_privacy') == consts.USER_PRIVACY_PRIVATE:
        flash(u"由于该用户设置了仅自己可见的权限，所以，我们就看不到了", "tip")
        return redirect(url_for("timeline"))

    return render_template("visual_timeline.html", user=u, unbinded=[], 
            config=config)

@app.route("/user/<uid>/timeline_json")
def timeline_json(uid):
    limit = 50
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = can_access_user(u)
    if r:
        abort(r[0], r[1])

    cate = request.args.get("cate", None)
    ids = Status.get_ids(user_id=u.id,
            start=g.start, limit=limit, cate=g.cate)
    ids = ids[::-1]

    status_list = Status.gets(ids)
    if g.user and g.user.id == uid:
        pass
    elif g.user and g.user.id != uid:
        status_list = [x for x in status_list if x.privacy() != consts.STATUS_PRIVACY_PRIVATE]
    elif not g.user:
        status_list = [x for x in status_list if x.privacy() == consts.STATUS_PRIVACY_PUBLIC]

    if not status_list:
        return json_encode({})

    date = []
    for s in status_list:
        headline = s.summary or ''
        text = ''
        images = s.get_data().get_images() or []
        
        if not (headline or text):
            continue

        t = s.create_time

        if s.category in [config.CATE_DOUBAN_STATUS, config.CATE_SINA_STATUS]:
            re_tweet = s.get_retweeted_data()
            re_images = re_tweet and re_tweet.get_images() or []
            images.extend(re_images)
            text = re_tweet and re_tweet.get_content() or ''

        if s.category in [config.CATE_QQWEIBO_STATUS]:
            text = s.get_retweeted_data() or ''
        
        if s.category in [config.CATE_WORDPRESS_POST]:
            uri = s.get_origin_uri()
            headline = '<a href="%s" target="_blank">%s</a>' % (uri and uri[1], s.title)
            text = s.text or ''
        
        tmp = {
            'startDate': t.strftime("%Y,%m,%d,%H,%M,%S"),
            'headline': headline,
            'text': text,
            'asset': {
                'media': images and images[0],
                'credit': '',
                'caption': ''
            },
        }
        try:
            json_encode(tmp)
            date.append(tmp)
        except:
            pass

    if date:
        tmp = {
            'startDate': datetime.now().strftime("%Y,%m,%d,%H,%M,%S"),
            'headline': '<a href="/user/%s/visual?start=%s">查看更早的内容...</a>' % (u.id, g.start+limit),
            'text': '',
            'asset': {
                'media': '', 'credit': '', 'caption': ''
            },
        }
        date.insert(0, tmp)

    json_data = {
        'timeline':
        {
            'headline': 'The past of you',
            'type': 'default',
            'startDate': date[1]['startDate'],
            'text': 'Storytelling about yourself...',
            'asset':{
                'media': '',
                'credit': '',
                'caption': ''
            },
            'date':date
        }
    }
    return json_encode(json_data)

@app.route("/i")
@require_login()
def timeline():
    return redirect("/user/%s?cate=%s" % (g.user.id, g.cate))

@app.route("/user/<uid>")
def user(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = can_access_user(u)
    if r:
        flash(r[1].decode("utf8"), "tip")
        return redirect(url_for("home"))

    ids = Status.get_ids(user_id=u.id, start=g.start, limit=g.count, cate=g.cate)
    status_list = Status.gets(ids)
    if g.user and g.user.id == uid:
        pass
    elif g.user and g.user.id != uid:
        status_list = [x for x in status_list if x.privacy() != consts.STATUS_PRIVACY_PRIVATE]
    elif not g.user:
        status_list = [x for x in status_list if x.privacy() == consts.STATUS_PRIVACY_PUBLIC]
        
    status_list  = statuses_timelize(status_list)
    if status_list:
        ##XXX:暂时去除了个人关键字的功能
        #tags_list = [x[0] for x in get_keywords(u.id, 30)]
        tags_list = []
    else:
        tags_list = []
    intros = [u.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)
    return render_template("timeline.html", user=u, unbinded=[], 
            tags_list=tags_list, intros=intros, status_list=status_list, config=config)

@app.route("/pdf")
@require_login()
def mypdf():
    if not g.user:
        return redirect(url_for("pdf", uid=config.MY_USER_ID))
    else:
        return redirect(url_for("pdf", uid=g.user.id))

@app.route("/demo-pdf")
def demo_pdf():
    pdf_filename = "demo.pdf"
    full_file_name = os.path.join(config.PDF_FILE_DOWNLOAD_DIR, pdf_filename)
    resp = make_response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % pdf_filename
    resp.headers['Content-Length'] = os.path.getsize(full_file_name)
    redir = '/down/pdf/' + pdf_filename
    resp.headers['X-Accel-Redirect'] = redir
    return resp
    
#PDF只允许登录用户查看
@app.route("/<uid>/pdf")
@require_login()
def pdf(uid):
    user = User.get(uid)
    if not user:
        abort(404, "No such user")

    if uid != g.user.id and user.get_profile_item('user_privacy') == consts.USER_PRIVACY_PRIVATE:
        flash(u"由于该用户设置了仅自己可见的权限，所以，我们就看不到了", "tip")
        return redirect(url_for("timeline"))

    intros = [g.user.get_thirdparty_profile(x).get("intro") for x in config.OPENID_TYPE_DICT.values()]
    intros = filter(None, intros)

    pdf_files = []
    start_date = Status.get_oldest_create_time(None, user.id)
    now = datetime.now()
    d = start_date
    while d and d <= now:
        pdf_filename = get_pdf_filename(user.id, d.strftime("%Y%m"))
        if is_pdf_file_exists(pdf_filename):
            full_file_name = get_pdf_full_filename(pdf_filename)
            pdf_files.append([d, pdf_filename, sizeof_fmt(os.path.getsize(full_file_name))])

        days = calendar.monthrange(d.year, d.month)[1]
        d += timedelta(days=days)
        d = datetime(d.year, d.month, 1)
    files_dict = defaultdict(list)
    for date, filename, filesize in pdf_files:
        files_dict[date.year].append([date, filename, filesize])
    return render_template("pdf.html", **locals())

@app.route("/pdf/<filename>")
@require_login()
def pdf_down(filename):
    pdf_filename = filename
    if not is_pdf_file_exists(pdf_filename):
        abort(404, "Please wait one day to  download the PDF version, because the vps memory is limited")

    user_id = pdf_filename.split('_')[1]
    u = User.get(user_id)
    if not u:
        abort(400, 'Bad request')

    if user_id != g.user.id and u.get_profile_item('user_privacy') == consts.USER_PRIVACY_PRIVATE:
        abort(403, 'Not allowed')

    full_file_name = get_pdf_full_filename(pdf_filename)
    resp = make_response()
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=%s' % pdf_filename
    resp.headers['Content-Length'] = os.path.getsize(full_file_name)
    redir = '/down/pdf/' + pdf_filename
    resp.headers['X-Accel-Redirect'] = redir
    return resp

## 把status_list构造为month，day的层级结构
def statuses_timelize(status_list):

    hashed = {}
    for s in status_list:
        hash_s = hash(s)
        if hash_s not in hashed:
            hashed[hash_s] = RepeatedStatus(s)
        else:
            hashed[hash_s].status_list.append(s)

    output = {}
    for hash_s, repeated in hashed.items():
        s = repeated.status_list[0]
        year_month = "%s-%s" % (s.create_time.year, s.create_time.month)
        day = s.create_time.day

        if year_month not in output:
            output[year_month] = {day:[repeated]}
        else:
            if day not in output[year_month]:
                output[year_month][day] = [repeated]
            else:
                output[year_month][day].append(repeated)

    return output

class RepeatedStatus(object):
    def __init__(self, status):
        self.create_time = status.create_time
        self.status_list = [status]
