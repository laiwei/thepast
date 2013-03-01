#-*- coding:utf-8 -*-
import hashlib
import xml.etree.ElementTree as ET
import time
import datetime

from flask import (session, redirect, request, abort, g, url_for, flash)
from past import config
from past import consts
from past.model.user import User
from past.model.weixin import UserWeixin
from past.model.status import Status, get_status_ids_today_in_history

from past.weixin import blue_print
from past.utils.logger import logging
log = logging.getLogger(__file__)

@blue_print.route("/callback", methods=["GET", "POST"])
def weixin_callback():
    #print "<<<method", request.method
    #print "<<<args:", request.args
    #print "<<<form:", request.form
    #print "<<<values:", request.values
    #print "<<<data:", request.data

    signature = request.args.get("signature", "")
    timestamp = request.args.get("timestamp", "")
    nonce = request.args.get("nonce", "")

    if not validate_sig(nonce, timestamp, signature):
        abort(400, "signature dismatch")

    if request.method == "GET":
        return request.args.get("echostr", "")

    elif request.method == "POST":
        content = request.data
        root = ET.fromstring(content)
        cmds = {}
        for x in root:
            cmds[x.tag] = x.text
        return echo(cmds)

def echo(cmds):
    msg_type = cmds.get("MsgType")
    if msg_type != "text":
        return ""

    content = cmds.get("Content")
    create_time = cmds.get("CreateTime")
    from_user = cmds.get("FromUserName")
    to_user = cmds.get("ToUserName")

    l = content.split()
    if not l:
        return ""

    reply_content = ""
    reply_type = "text"
    if l[0] == 'Hello2BizUser':
        reply_content = cmd_welcome()
    elif l[0] == 'h' or l[0] == 'help':
        reply_content = cmd_help()
    elif l[0] == 'b' or l[0] == 'bind':
        if len(l) == 1:
            reply_content = "你怎么没有提供thepast_id啊..."
        reply_content = cmd_bind(from_user, l[1])
    elif l[0] == 'p' or l[0] == 'past':
        
        if not UserWeixin.get_by_weixin(from_user):
            reply_content = "请先回复 bind thepast_id 告诉机器狗你的thepast_id是多少"
        else:
            reply_type = "news"
            if len(l) == 2:
                reply_content = cmd_past(from_user, l[1], reply_type)
            else:
                reply_content = cmd_past(from_user, "", reply_type)

    if not isinstance(reply_content, unicode):
        reply_content = reply_content.decode("utf8")
    reply_time = int(time.time())

    if reply_type == "text":
        reply_xml = u'''
            <xml>
             <ToUserName><![CDATA[{to_user}]]></ToUserName>
             <FromUserName><![CDATA[{from_user}]]></FromUserName>
             <CreateTime>{reply_time}</CreateTime>
             <MsgType><![CDATA[{reply_type}]]></MsgType>
             <Content><![CDATA[{reply_content}]]></Content>
             <FuncFlag>0</FuncFlag>
            </xml>'''.format(to_user=from_user, from_user=to_user, reply_time=reply_time, reply_type=reply_type, reply_content=reply_content)
    elif reply_type == "news":
        reply_xml = u'''
            <xml>
             <ToUserName><![CDATA[{to_user}]]></ToUserName>
             <FromUserName><![CDATA[{from_user}]]></FromUserName>
             <CreateTime>{reply_time}</CreateTime>
             <MsgType><![CDATA[{reply_type}]]></MsgType>
             {articles}
             <FuncFlag>1</FuncFlag>
            </xml>'''.format(to_user=from_user, from_user=to_user, reply_time=reply_time, reply_type=reply_type, articles=reply_content)
    print ">>>>> reply to %s" %from_user
    print reply_xml.encode("utf8")
    return reply_xml

def cmd_welcome():
    txt = "欢迎关注thepast^^\n%s" %cmd_help()
    return txt

def cmd_help():
    txt = '''现在，你面对的是，thepast.me的官方机器狗：）
输入
「help」 : 显示帮助信息
「bind thepast_id」 : 让机器狗知道你的thepast id
「past 02-28」  : 机器狗会回复你往年的这个日子，都发生了那些事情 '''

    return txt

def cmd_bind(from_user, thepast_id):
    u = User.get(thepast_id)
    if not u:
        return "不存在这个id啊，是不是搞错了啊"

    UserWeixin.add(u.id, from_user)
    return "绑定成功了，输入「past 日期」查看过往的碎碎念"

def cmd_past(from_user, date_, msg_type="text"):
    thepast_id = UserWeixin.get_by_weixin(from_user).user_id
    now = datetime.datetime.now()
    date_ = date_ or now.strftime("%m-%d") 
    date_ = "%s-%s" %(now.year + 1, date_)

    try:
        date_ = datetime.datetime.strptime(date_, "%Y-%m-%d")
    except:
        date_ = datetime.datetime(year=now.year+1, month=now.month, day=now.day)

    history_ids = get_status_ids_today_in_history(thepast_id, date_) 
    status_list = Status.gets(history_ids)
    status_list = [x for x in status_list if x.privacy() == consts.STATUS_PRIVACY_PUBLIC]

    r = ''
    if msg_type == "text":
        for x in status_list:
            r += x.create_time.strftime("%Y-%m-%d %H:%M") + "\n" + x.text + "\n~~~~~~~~~~\n"
    elif msg_type == "news":
        article_count = min(len(status_list)+1, 9)
        r += "<ArticleCount>%s</ArticleCount>" %article_count
        r += "<Articles>"
        date_str = u"{m}月{d}日".format(m=date_.month, d=date_.day)
        title0 = u"{d},找到{l}条往事,点击看更多".format(d=date_str, l=len(status_list))
        r += u'''
            <item>
            <Title><![CDATA[{title0}]]></Title> 
            <Description><![CDATA[{desc0}]]></Description>
            <PicUrl><![CDATA[{picurl0}]]></PicUrl>
            <Url><![CDATA[{url0}]]></Url>
            </item>
        '''.format(title0=title0, desc0="", picurl0="", url0="http://thepast.me/laiwei")

        for i in range(1, article_count):
            item_xml = '<item>'
            s = status_list[i-1]
            s_data = s.get_data()
            s_atts = s_data and s_data.get_attachments() or []
            s_images = s_data and s_data.get_images() or []

            s_re = s.get_retweeted_data()
            s_re_atts = s_re and s_re.get_attachments() or []
            s_re_images = s_re and s_re.get_images() or []
            s_re_user = s_re and s_re.get_user() or ""
            s_re_user_nickname = s_re_user if isinstance(s_re_user, basestring) else s_re_user.get_nickname()
            
            title = s.title

            desc = s.create_time.strftime("%Y-%m-%d %H:%M")
            desc += "\n" + s.summary
            for att in s_atts:
                desc += "\n" + att.get_href()
                desc += "\n" + att.get_description()
            if s_re_user_nickname and s_re.get_content():
                desc += "\n//@" + s_re_user_nickname + ":" + s_re.get_content()
            for att in s_re_atts:
                desc += "\n" + att.get_href()
                desc += "\n" + att.get_description()

            s_images.extend(s_re_images)
            pic_url = ""
            if s_images:
                pic_url = s_images[0]

            s_from = s.get_origin_uri()
            url = s_from and s_from[1] or pic_url

            item_xml += "<Title><![CDATA[" +title+desc+ "]]></Title>"
            item_xml += "<Description><![CDATA["+ title + desc +"]]></Description>"
            item_xml += "<PicUrl><![CDATA[" +pic_url+ "]]></PicUrl>"
            item_xml += "<Url><![CDATA[" +url+ "]]></Url>"
            item_xml += '</item>'
            r += item_xml

        r += "</Articles>"
    return r
   
def validate_sig(nonce, timestamp, signature, token="canuguess"):
    raw_str = "".join(sorted([str(nonce), str(timestamp), str(token)]))
    print "<<< raw_str:", raw_str
    enc = hashlib.sha1(raw_str).hexdigest()

    if enc and enc == signature:
        return True

    print "<<<invalid sig"
    return False
    
