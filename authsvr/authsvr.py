#!/usr/bin/env python
"""
simple fast persistent user authentication

Uses in memory lookups backed by a sqlite database

All these things return the same basic format:

success:
  { success: True, result: { ... } }

failure:
  { success: False, error: { message: "..." } }


"""
from gevent import monkey; monkey.patch_all()
import os, sys, traceback as tb, sqlite3
from bottle import request, Bottle, abort
from thekno.misc import add_cors_headers
from uuid import uuid1, uuid4

app = Bottle()

Users = dict() # in-memory cache
_conn = None   # storage for DB()

def DB():
    """
    get the static database connection
    """
    global _conn
    if not _conn:
        _conn = sqlite3.connect('auth.db')
        _conn.execute('''CREATE TABLE IF NOT EXISTS tokens (tok text, uid text)''')
        rs = _conn.execute('''SELECT tok,uid FROM tokens''')
        for row in rs:
            tok,uid = row
            Users[tok] = uid
            pass
        pass
    return _conn

@app.route('/')
def _():
    return ["Nothing to see here, move along..."]

@app.route('/verifyToken')
def verifyToken():
    """
    /verifyToken?token=<auth_token>

    is "token" valid?
    if so, get some basic info like the uid

    returns: { uid: <uid> }
    """
    add_cors_headers()

    tok = request.params.get('token')

    uid = Users.get(tok)
    if uid:
        result = {'success':True, 'result':{'uid':uid}}
    else:
        result = {'success':False,'error':{'message':'Not Found'}}
        pass
    return result

@app.route('/addUser')
def addUser():
    """
    /addUser?uid=<user_id>

    add in a user's access token

    returns: { uid: <uid> }
    """
    add_cors_headers()

    tok = str(uuid1())
    uid = request.params.get('uid')
    if not tok or not uid:
        return ['Missing uuid(u)\n']
    Users[tok] = uid
    DB().execute('INSERT INTO tokens (tok,uid) VALUES (?,?)', (tok, uid))
    DB().commit()
    return {'success':True, 'result':{'uid':uid,'token':tok}}

@app.route('/deleteUser')
def deleteUser():
    """/deleteUser?token=<auth_token>

    delete a user's access token

    returns: { uid: <uid> }
    """
    tok = request.params.get('token')
    Users.pop(tok,None)
    DB().execute('DELETE FROM tokens WHERE tok=?', (tok, ))
    DB().commit()
    return ['OK\n']

########################################################
# Facebook Stuff
########################################################

@app.route('/auth/callback/fb')
def _():
    print "GOT THE CALLBACK"
    add_cors_headers()
    print "001"
    return ['OK']

@app.route('/loginFB')
def _():
    print "000"
    add_cors_headers()
    print "001"

    from rauth import OAuth2Service

    facebook = OAuth2Service(
        client_id='852338521552385',
        client_secret='4639dfbad1a0bf5b22198ef705c2d9c8',
        name='facebook',
        authorize_url='https://graph.facebook.com/oauth/authorize',
        access_token_url='https://graph.facebook.com/oauth/access_token',
        base_url='https://graph.facebook.com/')

    print "FACEBOOK 1", facebook

    redirect_uri = 'https://www.facebook.com/connect/login_success.html'
    redirect_uri = 'http://kno.ccl.io:7777/auth/callback/fb'
    params = {'scope': 'read_stream',
              'response_type': 'code',
              'redirect_uri': redirect_uri}
    params = {'response_type': 'code',
              'redirect_uri': redirect_uri}

    url = facebook.get_authorize_url(**params)

    print "FACEBOOK 2", url

    return ["Hello"]

########################################################
# Main
########################################################

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

if __name__=='__main__':
    DB() # lazy evaluation is hard to debug
    server = WSGIServer(("0.0.0.0", 7777), app,
                        handler_class=WebSocketHandler)
    server.serve_forever()
