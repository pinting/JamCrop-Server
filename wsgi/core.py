#!/usr/bin/env python
#-*- coding: utf-8 -*-

__author__ = "Tornyi Dénes"
__version__ = "1.0.0"


KEY = '***REMOVED***'
SECRET = '***REMOVED***'


import poster.streaminghttp
import mimetypes
import urlparse
import urllib2
import oauth2
import urllib
import flask


app = flask.Flask(__name__)


def authorize():
    consumer = oauth2.Consumer(KEY, SECRET)
    client = oauth2.Client(consumer)
    response, content = client.request("https://api.dropbox.com/1/oauth/request_token", 'GET')
    return dict(urlparse.parse_qsl(content))


def access(request_token):
    token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    consumer = oauth2.Consumer(KEY, SECRET)
    client = oauth2.Client(consumer, token)
    response, content = client.request("https://api.dropbox.com/1/oauth/access_token", 'POST')
    return dict(urlparse.parse_qsl(content))


def sign(url, token, method = 'PUT', parameters = None):
    consumer = oauth2.Consumer(KEY, SECRET)
    request = oauth2.Request.from_consumer_and_token(consumer, token, method, url, parameters)
    request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    return request.to_url()


@app.route("/authorize", methods=['GET'])
def authorizePage():
    return str(urllib.urlencode(authorize()))


@app.route("/access", methods=['GET'])
def accessPage():

    """ Get an access token by the request token
    :get oauth_token: Token requested by the authorize page
    :get oauth_token_secret: Secret requested by the authorize page
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret'):
        access_token = access({'oauth_token': flask.request.args.get('oauth_token'),
                               'oauth_token_secret': flask.request.args.get('oauth_token_secret')})
        return str(urllib.urlencode(access_token))
    else:
        flask.abort(400)


@app.route("/upload", methods=['POST'])
def uploadPage():

    """ Upload screenshot to the server
    :http body: Body of the file
    :get oauth_token: Token requested by the authorize page
    :get oauth_token_secret: Secret requested by the authorize page
    :get name: Name of the file
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret') and \
       flask.request.args.get('name') and (mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/pjpeg' or
                                           mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/x-png' or
                                           mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/jpeg' or
                                           mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/png'):
        token = oauth2.Token(flask.request.args.get('oauth_token'), flask.request.args.get('oauth_token_secret'))
        headers = {'content-type': mimetypes.guess_type(flask.request.args.get('name'))[0],
                   'content-length': flask.request.headers.get('content-length')}
        url = sign("https://api-content.dropbox.com/1/files_put/sandbox/%s" %
                   flask.request.args.get('name'), token, 'PUT')

        opener = poster.streaminghttp.register_openers()
        request = urllib2.Request(url, flask.request.environ.get('wsgi.input')._rbuf, headers)
        request.get_method = lambda: 'PUT'
        content = opener.open(request)

        return content.read()
    else:
        flask.abort(400)


@app.route("/share", methods=['GET'])
def sharePage():

    """ Get the uploaded screenshot URL
    :get oauth_token: Token requested by the authorize page
    :get oauth_token_secret: Secret requested by the authorize page
    :get short: Length of the URL (if it is false, it will be long)
    :get name: Name of the file
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret') and \
       flask.request.args.get('short') and flask.request.args.get('name'):
        token = oauth2.Token(flask.request.args.get('oauth_token'), flask.request.args.get('oauth_token_secret'))
        url = sign("https://api.dropbox.com/1/shares/sandbox/%s?%s" % (flask.request.args.get('name'),
                   urllib.urlencode({'short_url': flask.request.args.get('short')})), token, 'POST')

        opener = poster.streaminghttp.register_openers()
        request = urllib2.Request(url)
        request.get_method = lambda: 'POST'
        content = opener.open(request)

        return content.read()
    else:
        flask.abort(400)


@app.route("/")
def mainPage():

    """ Redirect to home """

    return flask.redirect("https://code.google.com/p/jamcrop/")


if __name__ == "__main__":
    app.run(debug = True)

