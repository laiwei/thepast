#-*- coding:utf-8 -*- 
#-- db config --
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWD = "123456"
DB_NAME = "thepast"

#-- redis config --
#XXX
REDIS_HOST = "localhost"
REDIS_PORT = 6379

#XXX
REDIS_CACHE_HOST = "localhost"
REDIS_CACHE_PORT = 7379

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

##命名需要商榷
OPENID_WORDPRESS = 'wordpress'

OPENID_TYPE_DICT = {
    OPENID_DOUBAN : "D",
    OPENID_SINA : "S",
    OPENID_QQ : "Q",
    OPENID_TWITTER : "T",
    OPENID_WORDPRESS : "W",

    OPENID_THEPAST : "M",
}

OPENID_TYPE_NAME_DICT = {
    "D" : u"豆瓣",
    "S" : u"新浪微博",
    "T" : u"twitter",
    "Q" : u"腾讯微博",
    "W" : u"Wordpress",
    "M" : u"Thepast",
}

WELCOME_MSG_DICT = {
    "D": u"#thepast.me# 你好，旧时光 | 我在用thepast， 广播备份，往事提醒，你也来试试吧 >> http://thepast.me ",
    "S": u"#thepast.me# 你好，旧时光 | 我在用thepast， 微博备份，往事提醒，你也来试试吧 >> http://thepast.me ",
    "T": u"#thepast.me# 你好，旧时光 | 我在用thepast， twitter备份，往事提醒，你也来试试吧 >> http://thepast.me ",
    "Q": u"#thepast.me# 你好，旧时光 | 我在用thepast， 微博备份，往事提醒，你也来试试吧 >> http://thepast.me ",
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

CATE_LIST = (
    CATE_DOUBAN_NOTE,
    CATE_DOUBAN_MINIBLOG,
    CATE_SINA_STATUS,
    CATE_TWITTER_STATUS,
    CATE_QQWEIBO_STATUS,
    CATE_THEPAST_NOTE,
)

DOUBAN_NOTE = 'http://douban.com/note/%s'
DOUBAN_MINIBLOG = 'http://douban.com/people/%s/status/%s'
DOUBAN_STATUS = 'http://douban.com/people/%s/status/%s'
WEIBO_STATUS = 'http://weibo.com/%s'
QQWEIBO_STATUS = 'http://t.qq.com/t/%s'
TWITTER_STATUS = 'http://twitter.com/#!/%s/status/%s'
THEPAST_NOTE = 'http://thepast.me/note/%s'

DOUBAN_SITE = "http://www.douban.com"
SINA_SITE = "http://weibo.com"
TWITTER_SITE = "http://twitter.com/#!"
QQWEIBO_SITE = "http://t.qq.com"

#uid of laiwei
MY_USER_ID = 4

#cache
CACHE_DIR = "/home/work/proj/thepast/var/cache"

#file download 
FILE_DOWNLOAD_DIR = "/home/work/proj/thepast/var/down"
PDF_FILE_DOWNLOAD_DIR = FILE_DOWNLOAD_DIR + "/pdf"

#scws config
SCWS = "/usr/local/scws/bin/scws"
SCWS_XDB_DICT = "/usr/local/scws/etc/dict.utf8.xdb"
MY_CUT_DICT = "/home/work/proj/thepast/past/cws/mydict.txt"
HOT_TERMS_DICT = "/home/work/proj/thepast/past/cws/hot_terms.txt"

try:
    from local_config import *
except:
    import warnings
    warnings.warn('no local config')



