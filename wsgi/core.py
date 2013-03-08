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

    """ Get a request token from the Dropbox """

    consumer = oauth2.Consumer(KEY, SECRET)
    client = oauth2.Client(consumer)
    response, content = client.request("https://api.dropbox.com/1/oauth/request_token", 'GET')
    return dict(urlparse.parse_qsl(content))


def access(request_token):

    """ Get an access token from the Dropbox
    :param request_token: Recently got request token.
    """

    token = oauth2.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    consumer = oauth2.Consumer(KEY, SECRET)
    client = oauth2.Client(consumer, token)
    response, content = client.request("https://api.dropbox.com/1/oauth/access_token", 'POST')
    return dict(urlparse.parse_qsl(content))


def sign(url, token, method = 'PUT', parameters = None):

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


@app.route("/authorize", methods=['GET'])
def authorizePage():

    """ Show authorize page with GET method """

    return str(urllib.urlencode(authorize()))


@app.route("/access", methods=['GET'])
def accessPage():

    """ Show access page with GET method
    :urlparam oauth_token: Token requested by the authorize page
    :urlparam oauth_token_secret: Secret requested by the authorize page
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret'):
        access_token = access({'oauth_token': flask.request.args.get('oauth_token'),
                               'oauth_token_secret': flask.request.args.get('oauth_token_secret')})
        return str(urllib.urlencode(access_token))
    else:
        flask.abort(400)


@app.route("/upload", methods=['POST'])
def uploadPage():

    """ Show upload page with POST method
    :urlparam oauth_token: Token requested by the authorize page
    :urlparam oauth_token_secret: Secret requested by the authorize page
    :urlparam body: File body for upload
    :urlparam name: File name
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret') and \
       flask.request.files.get('body') and flask.request.args.get('name') and \
           (mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/jpeg' or
                    mimetypes.guess_type(flask.request.args.get('name'))[0] == 'image/pjpeg'):

        body = flask.request.files.get('body')
        headers = {'content-type': 'image/jpeg',
                   'content-length': str(len(body.read()))}
        token = oauth2.Token(flask.request.args.get('oauth_token'), flask.request.args.get('oauth_token_secret'))
        url = sign("https://api-content.dropbox.com/1/files_put/sandbox/%s" %
                   flask.request.args.get('name'), token, 'PUT')

        opener = poster.streaminghttp.register_openers()
        request = urllib2.Request(url, body.stream, headers)
        request.get_method = lambda: 'PUT'
        content = opener.open(request)

        body.close()
        return content.read()
    else:
        flask.abort(400)


@app.route("/share", methods=['GET'])
def sharePage():

    """ Show share page with GET method
    :urlparam oauth_token: Token requested by the authorize page
    :urlparam oauth_token_secret: Secret requested by the authorize page
    :urlparam short: Length of the URL (if it is false, it will be long)
    :urlparam name: File name
    """

    if flask.request.args.get('oauth_token') and flask.request.args.get('oauth_token_secret') and \
       flask.request.args.get('short') and flask.request.args.get('name'):
        token = oauth2.Token(flask.request.args.get('oauth_token'), flask.request.args.get('oauth_token_secret'))
        url = sign("https://api.dropbox.com/1/shares/sandbox/%s?%s" %
                        (flask.request.args.get('name'),
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

