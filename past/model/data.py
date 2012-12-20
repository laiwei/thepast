#-*- coding:utf-8 -*-

import re
import time
import datetime
import hashlib

from past import config
from past.utils.escape import json_decode , clear_html_element
from past.model.note import Note

## User数据接口 
class AbsUserData(object):

    def __init__(self, data):
        if data:
            self.data = data
        else:
            self.data = {}
        if isinstance(data, basestring):
            self.data = json_decode(data)

    def get_user_id(self):
        raise NotImplementedError

    def get_uid(self):
        raise NotImplementedError

    def get_nickname(self):
        return ""

    def get_intro(self):
        return ""

    def get_signature(self):
        return ""

    def get_avatar(self):
        return ""

    def get_icon(self):
        return ""
    
    def get_email(self):
        return ""

## 豆瓣user数据接口
class DoubanUser(AbsUserData):
    def __init__(self, data):
        super(DoubanUser, self).__init__(data)

    def get_user_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_uid(self):
        return self.data.get("uid", {}).get("$t")

    def get_nickname(self):
        return self.data.get("title", {}).get("$t")

    def get_intro(self):
        return self.data.get("content", {}).get("$t")

    def get_signature(self):
        return self.data.get("signature", {}).get("$t")

    def get_avatar(self):
        icon = self.get_icon()
        user_id = self.get_user_id()

        return icon.replace(user_id, "l%s" % user_id)

    def get_icon(self):
        links = {}
        _links = self.data.get("link", [])
        for x in _links:
            rel = x.get("@rel")
            links[rel] = x.get("@href")
        return links.get("icon", "")

## 豆瓣user2数据接口
class DoubanUser2(AbsUserData):
    def __init__(self, data):
        super(DoubanUser2, self).__init__(data)

    def get_user_id(self):
        return self.data.get("id")

    def get_uid(self):
        return self.data.get("uid")

    def get_nickname(self):
        return self.data.get("screen_name")

    def get_intro(self):
        return self.data.get("description")

    def get_signature(self):
        return ""

    def get_avatar(self):
        return self.data.get("large_avatar")

    def get_icon(self):
        return self.data.get("small_avatar")

## 新浪微博user数据接口
class SinaWeiboUser(AbsUserData):

    def __init__(self, data):
        super(SinaWeiboUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("idstr","")

    def get_uid(self):
        return self.data.get("domain", "")

    def get_nickname(self):
        return self.data.get("screen_name", "")

    def get_intro(self):
        return self.data.get("description", "")

    def get_signature(self):
        return ""

    def get_avatar(self):
        return self.data.get("avatar_large", "")

    def get_icon(self):
        return self.data.get("profile_image_url", "")

    def get_email(self):
        return ""

## Twitter user数据接口
class TwitterUser(AbsUserData):

    def __init__(self, data):
        super(TwitterUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("id_str","")

    def get_uid(self):
        return self.data.get("name", "")

    def get_nickname(self):
        return self.data.get("screen_name", "")

    def get_intro(self):
        return self.data.get("description", "")

    def get_signature(self):
        return ""

    def get_avatar(self):
        return self.data.get("profile_image_url", "")

    def get_icon(self):
        return self.data.get("profile_image_url", "")

    def get_email(self):
        return ""

## qq weibo user 数据接口
class QQWeiboUser(AbsUserData):

    def __init__(self, data):
        super(QQWeiboUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("openid","")

    def get_uid(self):
        return self.data.get("name", "")

    def get_nickname(self):
        return self.data.get("nick", "")

    def get_intro(self):
        return self.data.get("introduction", "")

    def get_signature(self):
        return ""

    def get_avatar(self):
        r = self.data.get("head", "")
        if r:
            return r + "/100"
        return r

    def get_icon(self):
        r = self.data.get("head", "")
        if r:
            return r + "/40"
        return r

    def get_email(self):
        return self.data.get("email", "")

    def get_birthday(self):
        return "%s-%s-%s" % (self.data.get("birth_year", ""),
            self.data.get("birth_month", ""), self.data.get("birth_day"))

## renren user数据接口
class RenrenUser(AbsUserData):

    def __init__(self, data):
        super(RenrenUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("uid","")

    def get_uid(self):
        return self.data.get("uid", "")

    def get_nickname(self):
        return self.data.get("name", "")

    def get_intro(self):
        return ""

    def get_signature(self):
        return ""

    def get_avatar(self):
        return self.data.get("headurl", "")

    def get_icon(self):
        return self.data.get("tinyurl", "")

    def get_email(self):
        return ""

## instagram user数据接口
class InstagramUser(AbsUserData):

    def __init__(self, data):
        super(InstagramUser, self).__init__(data)

    def get_user_id(self):
        return self.data.get("id","")

    def get_uid(self):
        return self.data.get("username", "")

    def get_nickname(self):
        return self.data.get("full_name", "") or self.get_uid()

    def get_intro(self):
        return self.data.get("bio", "")

    def get_signature(self):
        return self.data.get("website", "")

    def get_avatar(self):
        return self.data.get("profile_picture", "")

    def get_icon(self):
        return self.data.get("profile_picture", "")

    def get_email(self):
        return ""

## 第三方数据接口
class AbsData(object):
    
    def __init__(self, site, category, data):
        self.site = site
        self.category = category
        self.data = data or {}
        if isinstance(data, basestring):
            try:
                self.data = json_decode(data)
            except Exception, e:
                #import traceback; print traceback.format_exc()
                self.data = {}

    ## 注释以微博为例
    ##原始的数据，json_decode之后的
    def get_data(self):
        return self.data
    
    ##原微博的id
    def get_origin_id(self):
        raise NotImplementedError
    
    ##原微博的创建时间
    def get_create_time(self):
        raise NotImplementedError
    
    ##如果有title的话，比如豆瓣广播
    def get_title(self):
        return ""

    ##原微博的内容
    def get_content(self):
        return ""

    ##原微博本身是个转发，获取被转发的内容
    def get_retweeted_data(self):
        return None

    ##原微博附带的图片，返回结果为list
    def get_images(self):
        return []
    
    ##原微博的作者，如果能获取到的话
    ##XXX
    def get_user(self):
        return None

    ##原微博的uri，可以点过去查看（有可能获取不到或者很麻烦，比如sina就很变态）
    ###XXX
    def get_origin_uri(self):
        return ""

    ##摘要信息，对于blog等长文来说很有用,视情况在子类中覆盖该方法
    def get_summary(self):
        return self.get_content()

    ##lbs信息
    def get_location(self):
        return ""

    ##附件信息(暂时只有豆瓣的有)
    def get_attachments(self):
        return None

class ThepastNoteData(AbsData):
    
    def __init__(self, note):
        self.site = config.OPENID_TYPE_DICT[config.OPENID_THEPAST]
        self.category = config.CATE_THEPAST_NOTE
        self.data = note
        super(ThepastNoteData, self).__init__(
                self.site, self.category, self.data)

    def get_origin_id(self):
        return self.data and self.data.id

    def get_create_time(self):
        return self.data and self.data.create_time

    def get_title(self):
        return self.data and self.data.title or ""

    def get_content(self):
        if self.data:
            return self.data.render_content()
        return ""

    def get_origin_uri(self):
        if self.data:
            return config.THEPAST_NOTE % self.data.id
        return ""

    def get_summary(self):
        return self.data and self.data.content[:140]
        

class DoubanData(AbsData):
    
    def __init__(self, category, data):
        super(DoubanData, self).__init__( 
                config.OPENID_TYPE_DICT[config.OPENID_DOUBAN], category, data)

# 日记
class DoubanNoteData(DoubanData):
    def __init__(self, data):
        super(DoubanNoteData, self).__init__(
                config.CATE_DOUBAN_NOTE, data)

    def get_origin_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_create_time(self):
        return self.data.get("published",{}).get("$t")

    def get_title(self):
        return self.data.get("title", {}).get("$t") or ""

    def get_content(self):
        return self.data.get("content", {}).get("$t") or ""

# 广播
class DoubanMiniBlogData(DoubanData):
    def __init__(self, data):
        super(DoubanMiniBlogData, self).__init__(
                config.CATE_DOUBAN_MINIBLOG, data)

    def get_origin_id(self):
        id_ = self.data.get("id", {}).get("$t")
        if id_:
            return (id_.rstrip("/").split("/"))[-1]
        return None

    def get_create_time(self):
        return self.data.get("published",{}).get("$t")

    def get_title(self):
        return self.data.get("title", {}).get("$t") or ""

    def get_content(self):
        return self.data.get("content", {}).get("$t") or ""
    
    def _get_links(self):
        links = {}
        _links = self.data.get("link", [])
        for x in _links:
            rel = x.get("@rel")
            links[rel] = x.get("@href", "").replace("/spic", "/lpic")
        return links

    def get_images(self):
        links = self._get_links()
        if links and links.get("image"):
            return [links.get("image")]
        return []

# 豆瓣新广播（豆瓣说）
class DoubanStatusData(DoubanData):
    def __init__(self, data):
        super(DoubanStatusData, self).__init__(
            config.CATE_DOUBAN_STATUS, data)

    def _parse_score(self, title):
        r1 = title.find("[score]")
        r2 = title.find("[/score]")
        if r1 >= 0 and r2 >= 0:
            result = title[0:r1]
            star = int(title[r1+7:r2])
            for i in range(0, star):
                result += u"\u2605"
            result += title[r2+8:]
            return result
        else:
            return title

    def get_origin_id(self):
        return str(self.data.get("id", ""))

    def get_create_time(self):
        return self.data.get("created_at")

    def get_content(self):
        title = self.data.get("title", "")
        title = self._parse_score(title)
        return "%s %s" %(title, self.data.get("text", ""))

    def get_retweeted_data(self):
        r = self.data.get("reshared_status")
        if r:
            return DoubanStatusData(r)
        else:
            return None

    def get_images(self):
        o = []
        atts = self.get_attachments()
        for att in atts:
            medias = att and att.get_medias()
            for x in medias:
                if x and x.get_type() == 'image':
                    o.append(x.get_src().replace("http://img3", "http://img2").replace("http://img1", "http://img2").replace("http://img5", "http://img2"))   
        return o

    def get_user(self):
        r = self.data.get("user")
        if r:
            return DoubanUser2(r)
        else:
            return None

    def get_origin_uri(self):
        u = self.get_user()
        if u:
            uid = u.get_uid()
            return config.DOUBAN_STATUS % (uid, self.get_origin_id())

    ### 特有的方法：
    def get_target_type(self):
        return self.data.get("target_type")

    def get_attachments(self):
        rs = self.data.get("attachments", [])
        return [_Attachment(r) for r in rs]

class _Attachment(object):
    def __init__(self, data):
        self.data = data or {}

    def get_description(self):
        return self.data.get("description")
    def get_title(self):
        return self.data.get("title", "")
    def get_href(self):
        return self.data.get("expaned_href") or self.data.get("href")
    def get_medias(self):
        rs = self.data.get("media", [])
        return [_Media(x) for x in rs]


class _Media(object):
    def __init__(self, data):
        self.data = data or {}

    def get_type(self):
        return self.data.get("type")
    def get_src(self):
        src = self.data.get("original_src", "") or self.data.get("src", "")
        return src.replace("/spic/", "/mpic/").replace("/small/", "/raw/")
    
class SinaWeiboData(AbsData):
    
    def __init__(self, category, data):
        super(SinaWeiboData, self).__init__( 
                config.OPENID_TYPE_DICT[config.OPENID_SINA], category, data)

# 新浪微博status
class SinaWeiboStatusData(SinaWeiboData):
    def __init__(self, data):
        super(SinaWeiboStatusData, self).__init__(
                config.CATE_SINA_STATUS, data)
    
    def get_origin_id(self):
        return self.data.get("idstr", "")

    def get_create_time(self):
        try:
            t = self.data.get("created_at", "")
            return datetime.datetime.strptime(t, "%a %b %d %H:%M:%S +0800 %Y")
        except Exception, e:
            print e
            return None
    
    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text", "") 
    
    def get_retweeted_data(self):
        re = self.data.get("retweeted_status")
        if re:
            return SinaWeiboStatusData(re)

    def get_user(self):
        return SinaWeiboUser(self.data.get("user"))

    def get_origin_pic(self):
        return re.sub("ww[23456].sinaimg.cn", "ww1.sinaimg.cn", self.data.get("original_pic", ""))

    def get_thumbnail_pic(self):
        return re.sub("ww[23456].sinaimg.cn", "ww1.sinaimg.cn", self.data.get("thumbnail_pic", ""))

    def get_middle_pic(self):
        return re.sub("ww[23456].sinaimg.cn", "ww1.sinaimg.cn", self.data.get("bmiddle_pic", ""))

    def get_images(self, size="origin"):
        method = "get_%s_pic" % size
        if hasattr(self, method):
            i = getattr(self, method)()
            if i:
                return [i]
        return []
        
# twitter status
class TwitterStatusData(AbsData):
    def __init__(self, data):
        super(TwitterStatusData, self).__init__(
                config.OPENID_TYPE_DICT[config.OPENID_TWITTER], 
                config.CATE_TWITTER_STATUS, data)
    
    def get_origin_id(self):
        return str(self.data.get("id", ""))

    def get_create_time(self):
        t = self.data.get("created_at", "")
        return datetime.datetime.strptime(t, "%a %b %d %H:%M:%S +0000 %Y")

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text", "") 
    
    def get_retweeted_data(self):
        return None

    def get_user(self):
        return TwitterUser(self.data.get("user"))

    def get_origin_uri(self):
        u = self.get_user()
        if u:
            uid = u.get_user_id()
            status_id = self.get_origin_id()
            return config.TWITTER_STATUS % (uid, status_id)
        return None

# qqweibo status
class QQWeiboStatusData(AbsData):
    def __init__(self, data):
        super(QQWeiboStatusData, self).__init__(
                config.OPENID_TYPE_DICT[config.OPENID_QQ], 
                config.CATE_QQWEIBO_STATUS, data)
    
    def get_origin_id(self):
        return str(self.data.get("id", ""))

    def get_create_time(self):
        t = self.data.get("timestamp")
        if not t:
            return None
        t = float(t)
        return datetime.datetime.fromtimestamp(t)

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("text", "") 
    
    def get_retweeted_data(self):
        re = self.data.get("source")
        if re and re != 'null':
            return QQWeiboStatusData(re)
        else:
            return ""

    def get_user(self):
        return QQWeiboUser(self.data) 

    def _get_images(self, size):
        r = []
        imgs = self.data.get("image")
        if imgs and imgs != "null" and isinstance(imgs, list):
            r = ["%s/%s" % (x, size) for x in imgs]
        return r
        
    def get_origin_pic(self):
        return self._get_images(size=2000)

    def get_thumbnail_pic(self):
        return self._get_images(size=160)

    def get_middle_pic(self):
        return self._get_images(size=460)

    def get_images(self, size="middle"):
        method = "get_%s_pic" % size
        if hasattr(self, method):
            return getattr(self, method)()
        return []

    def get_origin_uri(self):
        return self.data.get("fromurl")


class WordpressData(AbsData):
    def __init__(self, data):
        super(WordpressData, self).__init__(
                config.OPENID_TYPE_DICT[config.OPENID_WORDPRESS],
                config.CATE_WORDPRESS_POST, data)

    def get_origin_id(self):
        id_ = self.data.get("id", "") or self.data.get("link", "")
        m = hashlib.md5()
        m.update(id_)
        return m.hexdigest()[:16]

    def get_create_time(self):
        e = self.data
        published = None
        try:
            published = e.published_parsed
        except AttributeError:
            try:
                published = e.updated_parsed
            except AttributeError:
                try:
                    published = e.created_parsed
                except AttributeError:
                    published = None
        if published:
            return datetime.datetime.fromtimestamp(time.mktime(published))
        
    
    def get_title(self):
        return self.data.get("title", "")

    def get_content(self):
        content = self.data.get("content")
        if content:
            c = content[0]
            return c and c.get("value")
        return ""

    def get_user(self):
        return self.data.get("author", "")

    def get_origin_uri(self):
        return self.data.get("link", "") or self.data.get("id", "")

    def get_summary(self):
        return clear_html_element(self.data.get("summary", ""))[:150]

class RenrenData(AbsData):
    
    def __init__(self, category, data):
        super(RenrenData, self).__init__( 
                config.OPENID_TYPE_DICT[config.OPENID_RENREN], category, data)

class RenrenStatusData(RenrenData):
    def __init__(self, data):
        super(RenrenStatusData, self).__init__(
                config.CATE_RENREN_STATUS, data)
    
    def get_origin_id(self):
        return str(self.data.get("status_id", ""))

    def get_create_time(self):
        return self.data.get("time")

    def get_title(self):
        return ""

    def get_content(self):
        return self.data.get("message", "") 
    
    def get_retweeted_data(self):
        d = {}
        d["status_id"] = self.data.get("root_status_id", "")
        forward_message = self.data.get("forward_message", "")
        root_message = self.data.get("root_message", "")
        if forward_message or root_message:
            d["message"] = "%s %s" %(forward_message, root_message)
        else:
            d["message"] = ""
        d["uid"] = self.data.get("root_uid", "")
        d["username"] = self.data.get("root_username", "")
        d["time"] = self.data.get("time", "")
        
        return RenrenStatusData(d)

    def get_user(self):
        return self.data.get("uid", "")

    def get_origin_uri(self):
        return "%s/%s#//status/status?id=%s" %(config.RENREN_SITE, self.data.get("uid"), self.data.get("uid"))

    def get_location(self):
        return self.data.get("place")

class RenrenFeedData(RenrenData):
    def __init__(self, data):
        super(RenrenFeedData, self).__init__(
                config.CATE_RENREN_FEED, data)
    
class RenrenBlogData(RenrenData):
    def __init__(self, data):
        super(RenrenBlogData, self).__init__(
                config.CATE_RENREN_BLOG, data)
    
    def get_origin_id(self):
        return str(self.data.get("id", ""))

    def get_create_time(self):
        return self.data.get("time")

    def get_title(self):
        return self.data.get("title", "")

    def get_content(self):
        return self.data.get("content", "") 

    def get_user(self):
        return self.data.get("uid", "")
    
    def get_origin_uri(self):
        return config.RENREN_BLOG %(self.get_user(), self.get_origin_id())
    
    def get_summary(self):
        c = self.get_content()
        if c and isinstance(c, basestring):
            return c[:140]
        return ""

class RenrenAlbumData(RenrenData):
    def __init__(self, data):
        super(RenrenAlbumData, self).__init__(
                config.CATE_RENREN_ALBUM, data)
    
    def get_origin_id(self):
        return str(self.data.get("aid", ""))

    def get_create_time(self):
        return self.data.get("create_time")

    def get_title(self):
        return self.data.get("name", "")

    def get_content(self):
        return self.data.get("description", "")

    def get_user(self):
        return self.data.get("uid", "")

    def get_images(self):
        return [self.data.get("url", "")]

    def get_size(self):
        return self.data.get("size", 100)
        

class RenrenPhotoData(RenrenData):
    def __init__(self, data):
        super(RenrenPhotoData, self).__init__(
                config.CATE_RENREN_PHOTO, data)
    
    def get_origin_id(self):
        return str(self.data.get("pid", ""))

    def get_create_time(self):
        return self.data.get("time")

    def get_title(self):
        return self.data.get("caption", "")

    def get_content(self):
        return ""

    def get_user(self):
        return self.data.get("uid", "")
    
    def get_origin_pic(self):
        return self.data.get("url_large", "")

    def get_thumbnail_pic(self):
        return self.data.get("url_tiny", "")

    def get_middle_pic(self):
        return self.data.get("url_head", "")

    def get_images(self, size="origin"):
        method = "get_%s_pic" % size
        r = []
        if hasattr(self, method):
            p = getattr(self, method)()
            if p:
                if not isinstance(p, list):
                    r.append(p)
                else:
                    r.extend(p)
        return r

class InstagramStatusData(AbsData):
    def __init__(self, data):
        super(InstagramStatusData, self).__init__(
                config.OPENID_TYPE_DICT[config.OPENID_INSTAGRAM], 
                config.CATE_INSTAGRAM_STATUS, data)
    
    def get_origin_id(self):
        return str(self.data.get("id", ""))

    def get_create_time(self):
        t = self.data.get("created_time")
        if not t:
            return None
        t = float(t)
        return datetime.datetime.fromtimestamp(t)

    def get_title(self):
        caption = self.data.get("caption")
        if caption and isinstance(caption, dict):
            return caption.get("text", "")
        return ""

    def get_content(self):
        return ""

    def get_user(self):
        udata = self.data.get("user")
        if udata and isinstance(udata, dict):
            return InstagramUser(udata)
    
    def get_origin_pic(self):
        images = self.data.get("images")
        if images:
            return images.get("standard_resolution",{}).get("url")

    def get_thumbnail_pic(self):
        images = self.data.get("images")
        if images:
            return images.get("thumbnail",{}).get("url")

    def get_middle_pic(self):
        images = self.data.get("images")
        if images:
            return images.get("low_resolution",{}).get("url")

    def get_images(self, size="origin"):
        method = "get_%s_pic" % size
        r = []
        if hasattr(self, method):
            p = getattr(self, method)()
            if p:
                if not isinstance(p, list):
                    r.append(p)
                else:
                    r.extend(p)
        return r

    def get_origin_uri(self):
        return self.data.get("link", "")

    def get_location(self):
        return self.data.get("location")
