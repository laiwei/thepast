#-*- coding:utf-8 -*-

#past.view.note

import markdown2
from flask import g, flash, request, render_template, redirect, abort
from past import app

from past.utils.escape import json_encode
from past.utils import randbytes
from past.api_client import Wordpress
from past.store import mc
from past.model.user import User
from past.model.note import Note
from past import consts
from past import config

from .utils import require_login

@app.route("/user/<uid>/notes", methods=["GET", "POST"])
@require_login()
def notes(uid):
    
    user = User.get(uid)
    if not user:
        abort(403, "no_such_user")

    note_ids = Note.get_ids_by_user(uid, g.start, g.count)
    notes = Note.gets(note_ids)

    return notes

@app.route("/note/<nid>", methods=["GET",])
def note(nid):
    note = Note.get(nid)
    if not note:
        abort(404, "no such note")

    title = note.title
    content = note.content
    fmt = note.fmt
    if fmt == consts.NOTE_FMT_MARKDOWN:
        content = markdown2.markdown(note.content)
    create_time = note.create_time
    return render_template("note.html", consts=consts, **locals())

@app.route("/note/edit/<nid>", methods=["GET", "POST"])
def note_edit(nid):
    note = Note.get(nid)
    if not note:
        abort(404, "no such note")

    if not g.user:
        abort(403, "please login first")
    if g.user.id != note.user_id:
        abort(403, "not edit privileges")
    
    error = ""
    if request.method == "GET":
        title = note.title
        content = note.content
        fmt = note.fmt
        return render_template("note_edit.html", consts=consts, **locals())
        
    elif request.method == "POST":
        # edit
        title = request.form.get("title", "")       
        content = request.form.get("content", "")
        fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)

        if request.form.get("cancel"):
            return redirect("/note/%s" % note.id)

        if request.form.get("submit"):
            error = check_note(title, content)
            if not error:
                note.update(title, content, fmt)
                flash(u"日记修改成功", "tip")
                return redirect("/note/%s" % note.id)
            else:
                flash(error.decode("utf8"), "error")
                return render_template("note_edit.html", consts=consts, **locals())
                
        else:
            return redirect("/note/%s" % note.id)
    

@app.route("/note/create", methods=["GET", "POST"])
@require_login()
def note_create():
    error = ""
    if request.method == "POST":

        title = request.form.get("title", "")       
        content = request.form.get("content", "")
        fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)

        if request.form.get("cancel"):
            return redirect("/i")
        
        # submit
        error = check_note(title, content)

        if not error:
            note = Note.add(g.user.id, title, content, fmt)
            if note:
                flash(u"日记写好了，看看吧", "tip")
                return redirect("/note/%s" % note.id)
            else:
                error = "添加日记的时候失败了，真不走运，再试试吧^^"
        if error:
            flash(error.decode("utf8"), "error")
            return render_template("note_create.html", **locals())

    elif request.method == "GET":
        return render_template("note_create.html", **locals())

    else:
        abort("wrong_http_method")

@app.route("/note/preview", methods=["POST"])
def note_preview():
    r = {}
    content = request.form.get("content", "")
    fmt = request.form.get("fmt", consts.NOTE_FMT_PLAIN)
    if fmt == consts.NOTE_FMT_MARKDOWN:
        r['data'] = markdown2.markdown(content)
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
