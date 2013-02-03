#!/usr/bin/env python
#-*- coding: utf-8 -*-

import webapp2, oauth2, httplib2, urlparse, urllib
from gaesessions import get_current_session

KEY = '***REMOVED***'
SECRET = '***REMOVED***'

class dropbox():
    def authorize(self):
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer)
        respone, content = client.request('https://api.dropbox.com/1/oauth/request_token', 'GET')
        return(dict(urlparse.parse_qsl(content)))
    
    def access(self, request_token):
        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer, token)
        respone, content = client.request('https://api.dropbox.com/1/oauth/access_token', "POST")
        return(dict(urlparse.parse_qsl(content)))
        
    def send(self, url, token, method = 'GET', parameters = {}):
        consumer = oauth2.Consumer(KEY, SECRET)
        request = oauth2.Request.from_consumer_and_token(consumer, token = token, http_method = method, http_url = url, parameters = parameters)
        request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
        return(httplib2.Http().request(request.to_url(), method))
        

class mainPage(webapp2.RequestHandler, dropbox):
    def get(self):
        session = get_current_session()
        session['request_token'] = self.authorize()
        self.response.write('<a href="%s?%s">Authorize application</a>' % ('https://www.dropbox.com/1/oauth/authorize', urllib.urlencode({'oauth_token' : session['request_token']['oauth_token'], 'oauth_callback' : self.request.host_url + '/info'})))
        
class membersPage(webapp2.RequestHandler, dropbox):
    def get(self):
        session = get_current_session()
        access_token = self.access(session['request_token'])
        token = oauth2.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
        self.response.write(self.send('https://api.dropbox.com/1/account/info', token))

app = webapp2.WSGIApplication([
    ('/', mainPage),
    ('/info', membersPage)
], debug = True)
