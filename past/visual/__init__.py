#-*- coding:utf-8 -*-
# blueprint: visual

from datetime import datetime, timedelta

from flask import Blueprint
from flask import redirect, render_template, g, abort, flash, url_for

from past import config, consts

from past.model.user import User
from past.model.status import Status

from past.utils.escape import json_encode
from past.view.utils import require_login, check_access_user

blue_print = Blueprint("visual", __name__, template_folder="templates", static_folder="static")

@blue_print.before_request
def before_request():
    pass

@blue_print.route("/")
@require_login(msg="登录后才能查看^^")
def myvisual():
    return redirect("/visual/%s" % g.user.id)

@blue_print.route("/<uid>")
@require_login(msg="登录后才能查看^^")
def visual(uid):
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = check_access_user(u)
    if r:
        flash(r[1].decode("utf8"), "tip")
        return redirect(url_for("timeline"))

    return render_template("visual_timeline.html", user=u, unbinded=[], 
            config=config)

@blue_print.route("/timeline.json/<uid>/<start>")
def timeline_json(uid, start):
    limit = 50
    start = int(start)
    u = User.get(uid)
    if not u:
        abort(404, "no such user")

    r = check_access_user(u)
    if r:
        abort(r[0], r[1])

    ids = Status.get_ids(user_id=u.id,
            start=start, limit=limit, cate=g.cate)
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
        headline = s.title or s.summary or ""
        text = s.text or ""
        data = s.get_data()
        images = data and data.get_images() or []

        uri = s.get_origin_uri()
        if uri:
            headline = '<a href="%s" target="_blank">%s</a>' % (uri and uri[1], headline)
        
        if not (headline or text or images):
            continue

        t = s.create_time

        if s.category in [config.CATE_DOUBAN_STATUS, config.CATE_SINA_STATUS]:
            re_tweet = s.get_retweeted_data()
            re_images = re_tweet and re_tweet.get_images() or []
            images.extend(re_images)
            text = re_tweet and re_tweet.get_content() or ''

        if s.category in [config.CATE_DOUBAN_STATUS]:
            atts = data and data.get_attachments()
            if atts:
                for att in atts:
                    text += att.get_title() + "\n" + att.get_description()

        if s.category in [config.CATE_QQWEIBO_STATUS]:
            text = s.get_retweeted_data() or ''
        
        if s.category in [config.CATE_WORDPRESS_POST, config.CATE_THEPAST_NOTE, config.CATE_RENREN_BLOG,]:
            uri = s.get_origin_uri()
            headline = '<a href="%s" target="_blank">%s</a>' % (uri and uri[1], s.title)
            text = s.text or ''

        if s.category in [config.CATE_RENREN_STATUS, config.CATE_RENREN_PHOTO, config.CATE_RENREN_ALBUM]:
            headline = s.title
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
        more = {
            'startDate': (status_list[-1].create_time - timedelta(0, 0, 1)).strftime("%Y,%m,%d,%H,%M,%S"),
            'headline': '<a href="/visual/%s?start=%s">查看更早的内容...</a>' % (u.id, start+limit),
            'text': '',
            'asset': {
                'media': '', 'credit': '', 'caption': ''
            },
        }
        date.append(more)

        if start == 0:
            cover = {
                'startDate': datetime.now().strftime("%Y,%m,%d,%H,%M,%S"),
                'headline': 'The past of you',
                'text': 'Storytelling about yourself...',
                'asset': {
                    'media': '', 'credit': '', 'caption': ''
                },
            }
            date.insert(0, cover)

    json_data = {
        'timeline':
        {
            'headline': 'The past of you',
            'type': 'default',
            'startDate': date[0]['startDate'],
            'text': 'Storytelling about yourself...',
            'asset':{
                'media': '',
                'credit': '',
                'caption': ''
            },

            'date':date,
        }
    }
    return json_encode(json_data)

