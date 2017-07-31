__author__ = 'kaneg'
import json

from flask import Flask, render_template, request, session, redirect, make_response

import settings
from lxd_mgr import LXDMgr
import os

app = Flask(__name__)
app.debug = settings.debug
app.secret_key = 'oruwdj2394jd9u3oquraurhcnmclkpcx;a439077&(&$(#YH,nz,cnuw93ej'

console_port_map = {}

lxd_mgr = None


def get_lxd_mgr():
    global lxd_mgr
    if not lxd_mgr:
        lxd_mgr = LXDMgr(settings.lxd_api_url,
                         (os.path.expanduser(settings.ssl_crt_path), os.path.expanduser(settings.ssl_key_path)))

    return lxd_mgr


def is_authorized():
    if not settings.login_required:
        return True
    auth = request.headers.get('Authorization')
    if auth and auth.startswith('Basic'):
        secret = auth.split(' ')[1].strip()
        origin = ('%s:%s' % (settings.admin_user, settings.admin_password)).encode('base64').strip()
        print repr(secret)
        print repr(origin)
        return secret == origin

    return False


from functools import wraps


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_authorized():
            return make_auth_rsp()
        else:
            return f(*args, **kwargs)

    def make_auth_rsp():
        rsp = make_response()
        rsp.headers['WWW-Authenticate'] = 'Basic realm="LXD Admin Realm"'
        rsp.status_code = 401
        return rsp

    return wrapper


@app.route('/console/<container>')
@login_required
def console(container):
    import urllib
    host, _ = urllib.splitport(request.host)
    vars = {
        'container': container,
        'host': host
    }
    console_url = settings.web_shell_host % vars

    return redirect(console_url)


@app.route('/')
@app.route('/list/')
@login_required
def lxd_list():
    context = {}
    lxds = get_lxd_mgr().list()
    image_aliases = get_lxd_mgr().list_image_alias()
    context['lxds'] = lxds
    context['lxd_image_aliases'] = image_aliases
    import status_codes
    context['StatusCodes'] = status_codes
    return render_template('lxd_list.html', **context)


@app.route('/create/<src>/<dst>')
@login_required
def create(src, dst):
    print 'from ', src, ' to ', dst
    r = json.dumps(get_lxd_mgr().create_from_image(dst, src))
    return r


@app.route('/copy/<src>/<dst>')
@login_required
def copy(src, dst):
    print src, ' to ', dst
    return json.dumps(get_lxd_mgr().create_from_container(dst, src))


@app.route('/start/<lxd>')
@login_required
def start(lxd):
    print 'start', lxd
    return json.dumps(get_lxd_mgr().start(lxd))


@app.route('/stop/<lxd>')
@login_required
def stop(lxd):
    print 'stop', lxd
    return json.dumps(get_lxd_mgr().stop(lxd))


@app.route('/delete/<lxd>')
@login_required
def delete(lxd):
    return json.dumps(get_lxd_mgr().delete(lxd))


if __name__ == '__main__':
    app.run(settings.server_host, port=settings.server_port)
