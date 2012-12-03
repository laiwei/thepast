#-*- coding:utf-8 -*-

#past.view.note

import markdown2
from flask import g, flash, request, render_template, redirect, abort, url_for
from past import app

from past.utils.escape import json_encode
from past.utils import randbytes
from past.store import mc
from past.model.user import User
from past.model.note import Note
from past import consts
from past import config

from .utils import require_login, check_access_note

@app.route("/notes", methods=["GET"])
@require_login()
def my_notes():
    return redirect("/%s?cate=%s" % (g.user.uid, config.CATE_THEPAST_NOTE))

@app.route("/<uid>/notes", methods=["GET"])
def user_notes(uid):
    user = User.get(uid)
    if not user:
        abort(403, "no_such_user")
    
    return redirect("/%s?cate=%s" % (uid, config.CATE_THEPAST_NOTE))

@app.route("/note/<nid>", methods=["GET",])
def note(nid):
    note = Note.get(nid)
    if not note:
        abort(404, "no such note")
    
    r = check_access_note(note)
    if r:
        flash(r[1].decode("utf8"), "tip")
        return redirect(url_for("home"))

    title = note.title
    content = note.content
    fmt = note.fmt
    if fmt == consts.NOTE_FMT_MARKDOWN:
        content = markdown2.markdown(note.content, extras=["wiki-tables", "code-friendly"])
    create_time = note.create_time
    user = User.get(note.user_id)
    return render_template("v2/note.html", consts=consts, **locals())

@app.route("/note/edit/<nid>", methods=["GET", "POST"])
@require_login()
def note_edit(nid):
    note = Note.get(nid)
    if not note:
        abort(404, "no such note")

    if g.user.id != note.user_id:
        abort(403, "not edit privileges")
    
    error = ""
    if request.method == "GET":
        title = note.title
        content = note.content
        fmt = note.fmt
        privacy = note.privacy
        return render_template("v2/note_create.html", consts=consts, **locals())
        
    elif request.method == "POST":
        # edit
        title = request.form.get("title", "")       
        content = request.form.get("content", "")
        fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)
        privacy = request.form.get("privacy", consts.STATUS_PRIVACY_PUBLIC)

        if request.form.get("cancel"):
            return redirect("/note/%s" % note.id)

        if request.form.get("submit"):
            error = check_note(title, content)
            if not error:
                note.update(title, content, fmt, privacy)
                flash(u"日记修改成功", "tip")
                return redirect("/note/%s" % note.id)
            else:
                flash(error.decode("utf8"), "error")
                return render_template("v2/note_create.html", consts=consts, **locals())
                
        else:
            return redirect("/note/%s" % note.id)
    
@app.route("/note/create", methods=["GET", "POST"])
@require_login(msg="先登录才能写日记")
def note_create():
    user = g.user
    error = ""
    if request.method == "POST":

        title = request.form.get("title", "")       
        content = request.form.get("content", "")
        fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)
        privacy = request.form.get("privacy", consts.STATUS_PRIVACY_PUBLIC)

        if request.form.get("cancel"):
            return redirect("/i")
        
        # submit
        error = check_note(title, content)

        if not error:
            note = Note.add(g.user.id, title, content, fmt, privacy)
            if note:
                flash(u"日记写好了，看看吧", "tip")
                return redirect("/note/%s" % note.id)
            else:
                error = "添加日记的时候失败了，真不走运，再试试吧^^"
        if error:
            flash(error.decode("utf8"), "error")
            return render_template("v2/note_create.html", consts=consts, **locals())

    elif request.method == "GET":
        return render_template("v2/note_create.html", consts=consts, **locals())

    else:
        abort("wrong_http_method")

@app.route("/note/preview", methods=["POST"])
def note_preview():
    r = {}
    content = request.form.get("content", "")
    fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)
    if fmt == consts.NOTE_FMT_MARKDOWN:
        r['data'] = markdown2.markdown(content, extras=["wiki-tables", "code-friendly"])
    else:
        r['data'] = content

    return json_encode(r)

def check_note(title, content):
    error = ""
    if not title:
        error = "得有个标题^^"
    elif not content:
        error = "写点内容撒^^"
    elif len(title) > 120:
        error = "标题有些太长了"
    elif len(content) > 102400:
        error = "正文也太长了吧"

    return error
