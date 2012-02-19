#-*- coding:utf-8 -*- 
#-- db config --
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWD = "123456"
DB_NAME = "thepast"

#-- redis config --
REDIS_HOST = "localhost"
REDIS_PORT = 6379

REDIS_CACHE_HOST = "localhost"
REDIS_CACHE_PORT = 7379

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
OPENID_WORDPRESS = 'wordpress'
OPENID_QQ = 'qq'
OPENID_GOOGLE = 'google'
OPENID_FACEBOOK = 'facebook'
OPENID_TWITTER = 'twitter'

OPENID_TYPE_DICT = {
    OPENID_DOUBAN : "D",
    OPENID_SINA : "S",
    OPENID_WORDPRESS : "W",
    OPENID_QQ : "Q",
    OPENID_GOOGLE : "G",
    OPENID_FACEBOOK : "F",
    OPENID_TWITTER : "T",
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
}

#-- category of status --
CATE_DOUBAN_STATUS = 100
CATE_DOUBAN_NOTE = 101
CATE_DOUBAN_MINIBLOG = 102
CATE_DOUBAN_PHOTO = 103
CATE_SINA_STATUS = 200
CATE_WORDPRESS_POST = 300
CATE_TWITTER_STATUS = 400

CATE_LIST = (
    CATE_DOUBAN_NOTE,
    CATE_DOUBAN_MINIBLOG,
    CATE_SINA_STATUS,
    CATE_TWITTER_STATUS,
)

DOUBAN_NOTE = 'http://douban.com/note/%s'
DOUBAN_MINIBLOG = 'http://douban.com/people/%s/status/%s'
WEIBO_STATUS = 'http://weibo.com/%s'
TWITTER_STATUS = 'http://twitter.com/%s'


DOUBAN_SITE = "http://www.douban.com"
SINA_SITE = "http://weibo.com"
TWITTER_SITE = "http://twitter.com"

#uid of laiwei
MY_USER_ID = 4

#cache
CACHE_DIR = "/home/work/proj/thepast/var/cache"

#file download 
FILE_DOWNLOAD_DIR = "/home/work/proj/thepast/var/down"
PDF_FILE_DOWNLOAD_DIR = FILE_DOWNLOAD_DIR + "/pdf"

try:
    from local_config import *
except:
    import warnings
    warnings.warn('no local config')



