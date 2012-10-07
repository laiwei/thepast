# -*- coding: utf-8 -*-

import tweepy
from tweepy.error import TweepError

from past import config
from past.utils.escape import json_encode, json_decode
from past.utils import httplib2_request

from past.model.user import User, UserAlias, OAuth2Token
from past.model.user import OAuth2Token
from past.model.data import TwitterUser
from past.model.data import TwitterStatusData

from .error import OAuthTokenExpiredError

class TwitterOAuth1(object):
    provider = config.OPENID_TWITTER

    def __init__(self, alias=None, 
            apikey=None, apikey_secret=None, redirect_uri=None,
            token=None, token_secret=None):

        d = config.APIKEY_DICT[config.OPENID_TWITTER]

        self.consumer_key = apikey or d['key']
        self.consumer_secret = apikey_secret or d['secret']
        self.callback = redirect_uri or d['redirect_uri']

        self.token = token
        self.token_secret = token_secret

        self.alias = alias
        if alias:
            self.user_alias = UserAlias.get(
                    config.OPENID_TYPE_DICT[config.OPENID_TWITTER], alias)
        else:
            self.user_alias = None

        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret, self.callback)
        if self.token and self.token_secret and self.auth:
            self.auth.set_access_token(self.token, self.token_secret)

    def __repr__(self):
        return "<TwitterOAuth1 consumer_key=%s, consumer_secret=%s, token=%s, token_secret=%s>" \
            % (self.consumer_key, self.consumer_secret, self.token, self.token_secret)
    __str__ = __repr__

    def login(self):
        return self.auth.get_authorization_url()

    def get_access_token(self, verifier=None):
        self.auth.get_access_token(verifier)
        t = {"access_token":self.auth.access_token.key, 
            "access_token_secret": self.auth.access_token.secret,}
        return t
    
    def save_request_token_to_session(self, session_):
        t = {"key": self.auth.request_token.key,
            "secret": self.auth.request_token.secret,}
        session_['request_token'] = json_encode(t)

    def get_request_token_from_session(self, session_, delete=True):
        t = session_.get("request_token")
        token = json_decode(t) if t else {}
        if delete:
            self.delete_request_token_from_session(session_)
        return token

    def delete_request_token_from_session(self, session_):
        session_.pop("request_token", None)

    @classmethod                                                                   
    def get_client(cls, user_id):                                                  
        alias = UserAlias.get_by_user_and_type(user_id,                            
                config.OPENID_TYPE_DICT[config.OPENID_TWITTER])                       
        if not alias:                                                              
            return None                                                            

        token = OAuth2Token.get(alias.id)
        if not token:
            return None
                                                                                   
        return cls(alias=alias.alias, token=token.access_token, token_secret=token.refresh_token)
    
    def api(self):
        return tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())

    def get_user_info(self):
        user = self.api().me()
        return TwitterUser(user)

    def get_timeline(self, since_id=None, max_id=None, count=200):
        user_id = self.user_alias and self.user_alias.user_id or None
        try:
            contents = self.api().user_timeline(since_id=since_id, max_id=max_id, count=count)
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_TWITTER], "")
            excp.clear_the_profile()
            return [TwitterStatusData(c) for c in contents]
        except TweepError, e:
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_TWITTER], 
                    "%s:%s" %(e.reason, e.response))
            excp.set_the_profile()
            raise excp

    def post_status(self, text):
        user_id = self.user_alias and self.user_alias.user_id or None
        try:
            self.api().update_status(status=text)
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_TWITTER], "")
            excp.clear_the_profile()
        except TweepError, e:
            excp = OAuthTokenExpiredError(user_id,
                    config.OPENID_TYPE_DICT[config.OPENID_TWITTER], 
                    "%s:%s" %(e.reason, e.response))
            excp.set_the_profile()
            raise excp

