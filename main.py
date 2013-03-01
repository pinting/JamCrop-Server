#!/usr/bin/env python
#-*- coding: utf-8 -*-

__author__ = "Tornyi Dénes"
__version__ = "1.0.0"


KEY = '***REMOVED***'
SECRET = '***REMOVED***'


import mimetypes
import httplib2
import urlparse
import webapp2
import oauth2
import urllib


class Dropbox():
    def authorize(self):

        """ Get a request token from the Dropbox """

        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer)
        respone, content = client.request("https://api.dropbox.com/1/oauth/request_token", 'GET')
        return dict(urlparse.parse_qsl(content))
    
    def access(self, request_token):

        """ Get an access token from the Dropbox
        :param request_token: Recently got request token.
        """

        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer, token)
        respone, content = client.request("https://api.dropbox.com/1/oauth/access_token", 'POST')
        return dict(urlparse.parse_qsl(content))
        
    def sign(self, url, token, method = 'PUT', parameters = None):

        """ Sign the give URL with oauth signature
        :param url: URL to sign
        :param token: Dropbox token
        :param method: HTTP method (POST, GET, etc.)
        :param parameters: Additional parameters
        """

        consumer = oauth2.Consumer(KEY, SECRET)
        request = oauth2.Request.from_consumer_and_token(consumer, token, method, url, parameters)
        request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
        return request.to_url()


class AuthorizePage(webapp2.RequestHandler, Dropbox):
    def get(self):

        """ Show authorize page with GET method """

        request_token = self.authorize()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(urllib.urlencode(request_token))


class AccessPage(webapp2.RequestHandler, Dropbox):
    def get(self):

        """ Show access page with GET method
        :urlparam oauth_token: Token requested by the authorize page
        :urlparam oauth_token_secret: Secret requested by the authorize page
        """

        if len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret')):
            access_token = self.access({'oauth_token': self.request.get('oauth_token'),
                                        'oauth_token_secret': self.request.get('oauth_token_secret')})
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(urllib.urlencode(access_token))
        else: self.error(400)


class UploadPage(webapp2.RequestHandler, Dropbox):
    def post(self):

        """ Show upload page with POST method
        :urlparam oauth_token: Token requested by the authorize page
        :urlparam oauth_token_secret: Secret requested by the authorize page
        :urlparam body: File body for upload
        :urlparam name: File name
        """

        if len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret')) and \
           len(self.request.get('body')) and len(self.request.get('name')):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            headers = {'content-type': mimetypes.guess_type(self.request.get('name')),
                       'content-length': str(len(self.request.get('body')))}
            url = self.sign("https://api-content.dropbox.com/1/files_put/sandbox/%s" %
                            self.request.get('name'), token, 'PUT')
            resp, content = httplib2.Http().request(url, 'PUT', body = self.request.get('body'), headers = headers)
        
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content)
        else: self.error(400)


class SharePage(webapp2.RequestHandler, Dropbox):
    def get(self):

        """ Show share page with GET method
        :urlparam oauth_token: Token requested by the authorize page
        :urlparam oauth_token_secret: Secret requested by the authorize page
        :urlparam short: Length of the URL (if it is false, it will be long)
        :urlparam name: File name
        """

        if len(self.request.get('oauth_token')) and len(self.request.get('oauth_token_secret')) and \
           len(self.request.get('short')) and len(self.request.get('name')):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            url = self.sign("https://api.dropbox.com/1/shares/sandbox/%s?%s" %
                            (self.request.get('name'),
                             urllib.urlencode({'short_url': self.request.get('short')})), token, 'POST')
            resp, content = httplib2.Http().request(url, 'POST')
        
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content)
        else: self.error(400)


app = webapp2.WSGIApplication([
    ('/authorize', AuthorizePage),
    ('/access', AccessPage),
    ('/upload', UploadPage),
    ('/share', SharePage),
    webapp2.Route('/', webapp2.RedirectHandler, defaults = {'_uri': 'https://code.google.com/p/jamcrop/'})
], debug = False)
