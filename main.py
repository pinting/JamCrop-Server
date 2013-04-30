#!/usr/bin/env python
#-*- coding: utf-8 -*-"""


"""
JamCropxy

If you have any advice, please write to us.
- Google Code: https://code.google.com/p/jamcrop/
"""


__author__ = "Dénes Tornyi"
__version__ = "1.1.0"


KEY = '***REMOVED***'
SECRET = '***REMOVED***'


from poster.streaminghttp import register_openers
import mimetypes
import urlparse
import webapp2
import urllib2
import oauth2
import urllib
import os


class Dropbox():
    def authorize(self):
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer)
        response, content = client.request("https://api.dropbox.com/1/oauth/request_token", 'GET')
        return dict(urlparse.parse_qsl(content))

    def access(self, request_token):
        token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        consumer = oauth2.Consumer(KEY, SECRET)
        client = oauth2.Client(consumer, token)
        response, content = client.request("https://api.dropbox.com/1/oauth/access_token", 'POST')
        return dict(urlparse.parse_qsl(content))

    def sign(self, url, token, method = 'PUT', parameters = None):
        consumer = oauth2.Consumer(KEY, SECRET)
        request = oauth2.Request.from_consumer_and_token(consumer, token, method, url, parameters)
        request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
        return request.to_url()


class AuthorizePage(webapp2.RequestHandler, Dropbox):
    def get(self):
        request_token = self.authorize()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(urllib.urlencode(request_token))


class AccessPage(webapp2.RequestHandler, Dropbox):
    def get(self):

        """ Get an access token by the request token
        :get oauth_token: Token requested by the authorize page
        :get oauth_token_secret: Secret requested by the authorize page
        """

        if self.request.get('oauth_token') and self.request.get('oauth_token_secret'):
            access_token = self.access({'oauth_token': self.request.get('oauth_token'),
                                        'oauth_token_secret': self.request.get('oauth_token_secret')})
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(urllib.urlencode(access_token))
        else:
            self.error(400)


class UploadPage(webapp2.RequestHandler, Dropbox, webapp2.Request):
    def post(self):

        """ Upload screenshot to the server
        :http body: Body of the file
        :get oauth_token: Token requested by the authorize page
        :get oauth_token_secret: Secret requested by the authorize page
        :get name: Name of the file
        """

        if self.request.get('oauth_token') and self.request.get('oauth_token_secret') and \
           self.request.get('name') and (mimetypes.guess_type(self.request.get('name'))[0] == 'image/jpeg' or
                                         mimetypes.guess_type(self.request.get('name'))[0] == 'image/png'):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            url = self.sign("https://api-content.dropbox.com/1/files_put/sandbox/%s" %
                            self.request.get('name'), token, 'PUT')
            headers = {'content-type': mimetypes.guess_type(self.request.get('name'))[0],
                       'content-length': self.response.headers["content-length"]}

            opener = register_openers()
            request = urllib2.Request(url, os.environ['wsgi.input'], headers)
            request.get_method = lambda: 'PUT'
            content = opener.open(request)

            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content.read())
        else:
            self.error(400)


class SharePage(webapp2.RequestHandler, Dropbox):
    def get(self):

        """ Get the uploaded screenshot URL
        :get oauth_token: Token requested by the authorize page
        :get oauth_token_secret: Secret requested by the authorize page
        :get short: Length of the URL (if it is false, it will be long)
        :get name: Name of the file
        """

        if self.request.get('oauth_token') and self.request.get('oauth_token_secret') and \
           self.request.get('short') and self.request.get('name'):
            token = oauth2.Token(self.request.get('oauth_token'), self.request.get('oauth_token_secret'))
            url = self.sign("https://api.dropbox.com/1/shares/sandbox/%s?%s" % (self.request.get('name'),
                             urllib.urlencode({'short_url': self.request.get('short')})), token, 'POST')

            opener = register_openers()
            request = urllib2.Request(url)
            request.get_method = lambda: 'POST'
            content = opener.open(request)

            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write(content.read())
        else:
            self.error(400)


app = webapp2.WSGIApplication([
    ('/authorize', AuthorizePage),
    ('/access', AccessPage),
    ('/upload', UploadPage),
    ('/share', SharePage),
    webapp2.Route('/', webapp2.RedirectHandler, defaults = {'_uri': 'https://code.google.com/p/jamcrop/'})
], debug = False)
