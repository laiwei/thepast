#-*- coding:utf-8 -*- 
#-- db config --
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWD = "123456"
DB_NAME = "thepast"

#-- smtp config --
SMTP_SERVER = "localhost"
SMTP_USER = ""
SMTP_PASSWORD = ""

#-- mc config --
# mc replace redis
MEMCACHED_HOST = "127.0.0.1"
MEMCACHED_PORT = 11211

#-- app config --
DEBUG = True
SECRET_KEY = "dev_key_of_thepast"
SESSION_COOKIE_NAME = "pastme"
PERMANENT_SESSION_LIFETIME = 3600 * 24 * 30

SITE_COOKIE = "pastck"

#-- class kind --#
K_SYNCTASK = 1000
K_TASKQUEUE = 1001

#-- openid type config --
OPENID_DOUBAN = 'douban'
OPENID_SINA = 'sina'
OPENID_QQ = 'qq' ##qq weibo
OPENID_TWITTER = 'twitter'
OPENID_THEPAST = 'thepast'
OPENID_RENREN = 'renren'
OPENID_INSTAGRAM = 'instagram'
##命名需要商榷
OPENID_WORDPRESS = 'wordpress'

OPENID_TYPE_DICT = {
    OPENID_DOUBAN : "D",
    OPENID_SINA : "S",
    OPENID_QQ : "Q",
    OPENID_TWITTER : "T",
    OPENID_WORDPRESS : "W",
    OPENID_THEPAST : "M",
    OPENID_RENREN: "R",
    OPENID_INSTAGRAM: "I",
}
OPENID_TYPE_DICT_REVERSE = dict((v,k) for k, v in OPENID_TYPE_DICT.iteritems())

OPENID_TYPE_NAME_DICT = {
    "D" : u"豆瓣",
    "S" : u"新浪微博",
    "T" : u"twitter",
    "Q" : u"腾讯微博",
    "W" : u"Wordpress",
    "M" : u"Thepast",
    "R" : u"人人",
    "I" : u"Instagram",
}

CAN_SHARED_OPENID_TYPE = [ "D", "S", "T", "Q", "R", "I", ]

wELCOME_MSG_DICT = {
    "D": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份广播，往事提醒  http://thepast.me ",
    "S": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份微博，往事提醒  http://thepast.me ",
    "T": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份twitter，往事提醒  http://thepast.me ",
    "Q": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份微博，往事提醒  http://thepast.me ",
    "R": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份人人，往事提醒  http://thepast.me ",
    "I": u"#thepast.me# 今天的点滴，就是明天的旧时光， thepast.me， 备份你的instagram，提醒往事  http://thepast.me ",
}

#-- oauth key & secret config --
APIKEY_DICT = {
    OPENID_DOUBAN : {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/douban/callback",
    },
    OPENID_SINA : {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/sina/callback",
    },
    OPENID_TWITTER : {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/twitter/callback",
    },
    OPENID_QQ: {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/qq/callback",
    },
    OPENID_RENREN: {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/renren/callback",
    },
    OPENID_INSTAGRAM: {
        "key" : "",
        "secret" : "",
        "redirect_uri" : "http://thepast.me/connect/instagram/callback",
    },
}

#-- category of status --
CATE_DOUBAN_STATUS = 100
CATE_DOUBAN_NOTE = 101
CATE_DOUBAN_MINIBLOG = 102
CATE_DOUBAN_PHOTO = 103
CATE_SINA_STATUS = 200
CATE_WORDPRESS_POST = 300
CATE_TWITTER_STATUS = 400
CATE_QQWEIBO_STATUS = 500
## thepast 的日记
CATE_THEPAST_NOTE = 600
CATE_RENREN_STATUS = 700
CATE_RENREN_FEED = 701
CATE_RENREN_BLOG = 702
CATE_RENREN_ALBUM = 703
CATE_RENREN_PHOTO = 704
CATE_INSTAGRAM_STATUS = 800

CATE_LIST = (
    CATE_DOUBAN_NOTE,
    CATE_DOUBAN_MINIBLOG,
    CATE_SINA_STATUS,
    CATE_TWITTER_STATUS,
    CATE_QQWEIBO_STATUS,
    CATE_THEPAST_NOTE,
    CATE_RENREN_STATUS,
    CATE_RENREN_FEED,
    CATE_RENREN_BLOG,
    CATE_RENREN_ALBUM,
    CATE_RENREN_PHOTO,
    CATE_INSTAGRAM_STATUS,
)

DOUBAN_NOTE = 'http://douban.com/note/%s'
DOUBAN_MINIBLOG = 'http://douban.com/people/%s/status/%s'
DOUBAN_STATUS = 'http://douban.com/people/%s/status/%s'
WEIBO_STATUS = 'http://weibo.com/%s'
QQWEIBO_STATUS = 'http://t.qq.com/t/%s'
TWITTER_STATUS = 'http://twitter.com/#!/%s/status/%s'
THEPAST_NOTE = 'http://thepast.me/note/%s'
RENREN_BLOG = 'http://blog.renren.com/blog/%s/%s'
INSTAGRAM_USER_PAGE = 'http://instagram.com/%s'

DOUBAN_SITE = "http://www.douban.com"
SINA_SITE = "http://weibo.com"
TWITTER_SITE = "http://twitter.com"
QQWEIBO_SITE = "http://t.qq.com"
RENREN_SITE = "http://www.renren.com"
INSTAGRAM_SITE = "http://instagram.com"

#uid of laiwei
MY_USER_ID = 4

#cache
CACHE_DIR = "/home/work/proj/thepast/var/cache"

#file download 
FILE_DOWNLOAD_DIR = "/home/work/proj/thepast/var/down"
PDF_FILE_DOWNLOAD_DIR = FILE_DOWNLOAD_DIR + "/pdf"

#suicide log
SUICIDE_LOG = "/home/work/proj/thepast/suicide.log"

try:
    from local_config import *
except:
    import warnings
    warnings.warn('no local config')



