"""
bottle-pxsession is a secure pickle based session library,
https://github.com/promek/bottle-pxsession
License: MIT (see LICENSE for details)
"""
__author__ = 'ibrahim SEN'
__version__ = '0.1.0'
__license__ = 'MIT'

import inspect
from bottle import PluginError,request,response,cookie_encode,cookie_decode
import uuid
import pickle
import os
import time

try:
    from Crypto.Random import get_random_bytes
    def getUuid():
        return uuid.UUID(bytes=get_random_bytes(16))

except ImportError:
    def getUuid():
        return uuid.uuid4()

MAX_TTL = 7*24*3600 # 7 day maximum cookie limit for sessions

class SessionPlugin(object):
    name = 'session'
    api = 2

    def __init__(self,session_dir="/tmp",session_key=None,cookie_name='px.session',cookie_lifetime=300,keyword='session'):
        self.session_dir = session_dir
        self.session_key = session_key
        self.cookie_name = cookie_name
        self.cookie_lifetime = cookie_lifetime
        self.keyword = keyword

    def setup(self,app):
        for other in app.plugins:
            if not isinstance(other, SessionPlugin): continue
            if other.keyword == self.keyword:
                raise PluginError("Found another session plugin with "\
                        "conflicting settings (non-unique keyword).")

    def apply(self,callback,context):
        conf = context.config.get('session') or {}
        args = inspect.getargspec(context.callback)[0]

        if self.keyword not in args:
            return callback

        def wrapper(*args,**kwargs):
            kwargs[self.keyword] = Session(self.session_dir,self.session_key,self.cookie_name,self.cookie_lifetime)
            rv = callback(*args,**kwargs)
            return rv
        return wrapper


class Session(object):

    def __init__(self,session_dir="/tmp",session_key=None,cookie_name='px.session',cookie_lifetime=None):
        self.session_dir = session_dir
        self.cookie_name = cookie_name
        self.session_key = session_key
        if cookie_lifetime is None:
            self.ttl = MAX_TTL
            self.max_age = None
        else:
            self.ttl = cookie_lifetime
            self.max_age = cookie_lifetime

        cookie_value = self.get_cookie()
        self.data = None
        if cookie_value:
            self.load_session(cookie_value)
        else:
            self.new_session()

    def get_cookie(self):
        uid_cookie = request.get_cookie(self.cookie_name,secret=self.session_key)
        return uid_cookie

    def set_cookie(self,value):
        response.set_cookie(self.cookie_name,value,secret=self.session_key,max_age=self.max_age,path='/')

    def get_session(self):
        return self.load_session(self.cookie_value)

    def load_session(self,cookie_value):
        self.sessionid = uuid.UUID(cookie_value).hex
        fileName = os.path.join(self.session_dir, 'sess-px-%s' % self.sessionid)
        if os.path.exists(fileName):
            with open(fileName, 'r') as fp:
                if self.session_key is None :
                    self.data = pickle.load(fp)
                else :
                    self.data = cookie_decode(fp.read(),self.session_key)
        else:
            self.new_session()

    def new_session(self):
        uid = getUuid()
        self.sessionid = uid.hex
        self.set_cookie(self.sessionid)
        self.data = {'_ttl':self.ttl,'_utm':time.time(),'_sid': self.sessionid}
        self.save()

    def save(self):
        fileName = os.path.join(self.session_dir, 'sess-px-%s' % self.sessionid)
        with open(fileName, 'w') as fp:
            if self.session_key is None :
                pickle.dump(self.data, fp)
            else :
                fp.write(cookie_encode(self.data,self.session_key))

    def expire(self):
        now=time.time()
        if self.data['_utm'] > (now-self.data['_ttl']) :
            self.data['_utm']=now
        else:
            self.regenerate()

    def destroy(self):
        fileName = os.path.join(self.session_dir, 'sess-px-%s' % self.sessionid)
        if os.path.exists(fileName):
            os.remove(fileName)
        response.delete_cookie(self.cookie_name)

    def regenerate(self):
        self.destroy()
        self.new_session()

    def __contains__(self,key):
        if key in self.data :
            return True
        else :
            return False

    def __delitem__(self,key):
        del self.data[key]

    def __getitem__(self,key):
        self.expire()
        if key in self.data :
            return self.data[key]
        else :
            return None

    def __setitem__(self,key,value):
        self.expire()
        self.data[key]=value

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for t in self.data.items():
            yield t

    def get(self,key,default=None):
        retval = self.__getitem__(key)
        if retval == None:
            retval = default
        return retval

    def has_key(self,key):
        return self.__contains__(key)

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()
