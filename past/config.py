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


#-- app config --
DEBUG = True
SECRET_KEY = "dev_key_of_thepast"
SESSION_COOKIE_NAME = "pastme"

SITE_COOKIE = "pastck"

#-- openid type config --
OPENID_DOUBAN = 'douban'
OPENID_SINA = 'sina'
OPENID_QQ = 'qq'
OPENID_GOOGLE = 'google'
OPENID_FACEBOOK = 'facebook'
OPENID_TWITTER = 'twitter'

OPENID_TYPE_DICT = {
    OPENID_DOUBAN : "D",
    OPENID_SINA : "S",
    OPENID_QQ : "Q",
    OPENID_GOOGLE : "G",
    OPENID_FACEBOOK : "F",
    OPENID_TWITTER : "T",
}

CATE_DOUBAN_STATUS = 100
CATE_DOUBAN_NOTE = 101
CATE_DOUBAN_PHOTO = 102
CATE_SINA_STATUS = 200
CATE_WORDPRESS_POST = 300
CATE_TWITTER_STATUS = 400

#-- oauth key & secret config --
APIKEY_DICT = {
    OPENID_DOUBAN : {
        "key" : "047e255f2309478c0d7a701d691bd6a4",
        "secret" : "0253348fa4d10541",
        "redirect_uri" : "http://127.0.0.1:5000/connect/douban/callback",
    },
}

#-- sync kind --
SYNC_DOUBAN_SHUO = 'db_s'
SYNC_DOUBAN_NOTE = 'db_n'
