__author__ = 'kaneg'
import json

from flask import Flask, render_template, request, session, redirect, make_response

import settings
from lxd_mgr import LXDMgr
import os
import status_codes

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


def is_authorized(action):
    if not settings.login_required:
        return True
    auth = request.headers.get('Authorization')
    if auth and auth.startswith('Basic'):
        secret = auth.split(' ')[1].strip()
        up = secret.decode('base64')
        username, pwd = up.split(':')
        if username == settings.admin_user:
            return pwd == settings.admin_password
        else:
            users = settings.get_users()
            if username in users:
                user = users[username]
                if user['password'] == pwd:
                    return user['permission'] and action in user['permission']
    return False


from functools import wraps


def make_auth_rsp():
    rsp = make_response()
    rsp.headers['WWW-Authenticate'] = 'Basic realm="LXD Admin Realm"'
    rsp.status_code = 401
    return rsp


def login_required(f, action):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print 'wrapper action:', action
        if not is_authorized(action):
            return make_auth_rsp()
        else:
            return f(*args, **kwargs)

    return wrapper


def check_permission(action):
    def wrapper(f):
        return login_required(f, action)

    return wrapper


@app.route('/logout')
def logout():
    return make_auth_rsp()


@app.route('/console/<container>')
@check_permission('console')
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
@check_permission('list')
def lxd_list():
    context = {}
    lxds = get_lxd_mgr().list()
    image_aliases = get_lxd_mgr().list_image_alias()
    context['lxds'] = lxds
    context['lxd_image_aliases'] = image_aliases
    context['StatusCodes'] = status_codes
    context['navigation'] = 'container'
    return render_template('lxd_list.html', **context)


@app.route('/create/<src>/<dst>')
@check_permission('create')
def create(src, dst):
    print 'from ', src, ' to ', dst
    r = json.dumps(get_lxd_mgr().create_from_image(dst, src))
    return r


@app.route('/copy/<src>/<dst>')
@check_permission('copy')
def copy(src, dst):
    print src, ' to ', dst
    return json.dumps(get_lxd_mgr().create_from_container(dst, src))


@app.route('/start/<lxd>')
@check_permission('start')
def start(lxd):
    print 'start', lxd
    return json.dumps(get_lxd_mgr().start(lxd))


@app.route('/stop/<lxd>')
@check_permission('stop')
def stop(lxd):
    print 'stop', lxd
    return json.dumps(get_lxd_mgr().stop(lxd))


@app.route('/delete/<lxd>')
@check_permission('delete')
def delete(lxd):
    return json.dumps(get_lxd_mgr().delete(lxd))


@app.route('/image/')
@app.route('/image/list/')
@check_permission('image_list')
def lxd_image_list():
    context = {}
    images = get_lxd_mgr().list_images()
    context['lxd_images'] = images
    context['StatusCodes'] = status_codes
    context['navigation'] = 'image'
    return render_template('image_list.html', **context)


@app.route('/image/edit/<image>', methods=['POST'])
@check_permission('image_edit')
def lxd_image_edit(image):
    print image
    print request.form
    image_name = request.form['image_name']
    image_description = request.form['image_description']
    data = {
        "properties": {
            "name": image_name,
            "description": image_description
        }
    }
    return json.dumps(get_lxd_mgr().image_edit(image, data))


if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(settings.server_host, port=settings.server_port, threaded=10)
