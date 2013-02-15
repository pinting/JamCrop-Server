#!/usr/bin/env python
#-*- coding: utf-8 -*-

import webapp2, oauth2, httplib2, urlparse, urllib, mimetypes

KEY = '***REMOVED***'
SECRET = '***REMOVED***'

class dropbox():
    def authorize(self):
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer)
        respone, content = client.request("https://api.dropbox.com/1/oauth/request_token", 'GET')
        return(dict(urlparse.parse_qsl(content)))
    
    def access(self, request_token):
        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer, token)
        respone, content = client.request("https://api.dropbox.com/1/oauth/access_token", 'POST')
        return(dict(urlparse.parse_qsl(content)))
        
    def sign(self, url, token, method = 'PUT', parameters = {}):
        consumer = oauth2.Consumer(KEY, SECRET)
        request = oauth2.Request.from_consumer_and_token(consumer, http_method = method, token = token, http_url = url, parameters = parameters)
        request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
        return(request.to_url())
        

class pageAuthorize(webapp2.RequestHandler, dropbox):
    def get(self):
        request_token = self.authorize()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(urllib.urlencode(request_token))
        
class pageAccess(webapp2.RequestHandler, dropbox):
    def get(self):
        if(len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret'))):
            access_token = self.access({'oauth_token' : self.request.get('oauth_token'), 'oauth_token_secret' : self.request.get('oauth_token_secret')})
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(urllib.urlencode(access_token))
        else: self.error(400)
        
class pageUpload(webapp2.RequestHandler, dropbox):
    def post(self):
        if(len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret')) 
        and len(self.request.get('body')) and len(self.request.get('name'))):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            headers = {'content-type' : mimetypes.guess_type(self.request.get('name')), 'content-length' : str(len(self.request.get('body')))}
            url = self.sign("https://api-content.dropbox.com/1/files_put/sandbox/%s" % self.request.get('name'), token, 'PUT')
            resp, content = httplib2.Http().request(url, 'PUT', body = self.request.get('body'), headers = headers)
        
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content)
        else: self.error(400)
        
class pageShare(webapp2.RequestHandler, dropbox):
    def get(self):
        if(len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret')) 
        and len(self.request.get('short')) and len(self.request.get('name'))):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            url = self.sign("https://api.dropbox.com/1/shares/sandbox/%s?%s" % (self.request.get('name'), 
                            urllib.urlencode({'short_url' : self.request.get('short')})), token, 'POST')
            resp, content = httplib2.Http().request(url, 'POST')
        
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content)
        else: self.error(400)

app = webapp2.WSGIApplication([
    ('/authorize', pageAuthorize),
    ('/access', pageAccess),
    ('/upload', pageUpload),
    ('/share', pageShare),
    webapp2.Route('/', webapp2.RedirectHandler, defaults = {'_uri' : 'https://code.google.com/p/jamcrop/'})
], debug = False)
