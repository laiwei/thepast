# -*- coding: utf-8 -*-
import datetime
from tweepy.error import TweepError
from past.model.user import User

class OAuthError(Exception):
    KEY_PREFIX = "OE"
    def __init__(self, msg_type, user_id, openid_type, msg):
        self.msg_type = msg_type
        self.user_id = user_id
        self.openid_type = openid_type
        self.msg = msg

    def __str__(self):
        return "user:%s, openid_type:%s, %s, %s" % \
            (self.user_id, self.openid_type, self.msg_type, self.msg)
    __repr__ = __str__

    def set_the_profile(self):
        u = User.get(self.user_id)
        if u:
            u.set_thirdparty_profile_item(self.openid_type, self.msg_type, datetime.datetime.now())

    def clear_the_profile(self):
        u = User.get(self.user_id)
        if u:
            u.set_thirdparty_profile_item(self.openid_type, self.msg_type, "")

    def is_error_exists(self):
        u = User.get(self.user_id)
        return u and u.get_thirdparty_profile(self.openid_type)

class OAuthTokenExpiredError(OAuthError):
    TYPE = "expired"
    def __init__(self, user_id=None, openid_type=None, msg=""):
        super(OAuthTokenExpiredError, self).__init__(
            OAuthTokenExpiredError.TYPE, user_id, openid_type, msg)

class OAuthAccessError(OAuthError):
    TYPE = "access_error"
    def __init__(self, user_id=None, openid_type=None, msg=""):
        super(OAuthAccessError, self).__init__(
            OAuthTokenExpiredError.TYPE, user_id, openid_type, msg)


class OAuthLoginError(OAuthError):
    TYPE = "login"
    def __init__(self, user_id=None, openid_type=None, msg=""):
        if isinstance(msg, TweepError):
            msg = "%s:%s" %(msg.reason, msg.response) 
        super(OAuthLoginError, self).__init__(
            OAuthLoginError.TYPE, user_id, openid_type, msg)

