__author__ = 'kaneg'
from flask import json
import requests
import unixsocket
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL_CONTAINERS = '%(version)s/containers'
API_URL_CONTAINER = '%(version)s/containers/%(container)s'
API_URL_CONTAINER_STATE = '%(version)s/containers/%(container)s/state'
API_URL_IMAGES = '%(version)s/images'
API_URL_IMAGE_ALIASES = '%(version)s/images/aliases'
API_URL_IMAGE = '%(version)s/images/%(image)s'
API_URL_IMAGE_ALIAS = '%(version)s/images/aliases/%(alias)s'


class LXDMgr(object):
    def __init__(self, api_url, cert=None):
        super(LXDMgr, self).__init__()
        self.base_url = api_url
        # print self.base_url
        session = requests.Session()
        session.verify = False
        session.cert = cert
        if 'unix:' in api_url:
            session.mount('unix:', unixsocket.UnixAdapter())
        rsp = session.get(self.base_url)
        # print rsp
        r = rsp.json()
        if self.is_success(r):
            self.version = r['metadata'][0]
            self.session = session
        else:
            raise Exception('Initiate lxd manager failed.', rsp.status_code, r)

    def get_url(self, tpl, *param):
        base_info = {'version': self.version}
        base_info.update(*param)
        url = tpl % base_info
        # print url
        return url

    def join_url(self, *path):
        url = self.base_url + '/'.join(path)
        return url

    def to_url(self, tpl, *param):
        url = self.join_url(self.get_url(tpl, *param))
        # print url
        return url

    @staticmethod
    def is_success(result):
        return result and not result['error_code'] and result['status_code'] == 200

    def list(self):
        result = self.session.get(self.to_url(API_URL_CONTAINERS)).json()
        if self.is_success(result):
            container_url_list = result['metadata']
            containers = map(self.get_container_by_url, container_url_list)
            for container in containers:
                container['state'] = self.get_state(container['name'])
            return containers
        return []

    def get_container_by_url(self, path):
        r = self.session.get(self.join_url(path))
        # print r.text
        result = r.json()
        if self.is_success(result):
            return result['metadata']

    def get_alias_by_url(self, url):
        m = self.session.get(self.join_url(url)).json()['metadata']
        target = m['target']
        return m['name'], self.get_image_by_id(target)

    def list_image_alias(self):
        r = self.session.get(self.to_url(API_URL_IMAGE_ALIASES)).json()
        if self.is_success(r):
            aliases = r['metadata']
            images = map(self.get_alias_by_url, aliases)
            result = {}
            result.update(images)
            return result
        return {}

    def get_image_by_url(self, url):
        image = self.session.get(self.join_url(url)).json()['metadata']
        return image

    def list_images(self):
        r = self.session.get(self.to_url(API_URL_IMAGES)).json()
        if self.is_success(r):
            image_urls = r['metadata']
            return map(self.get_image_by_url, image_urls)
        return []

    def get_image_by_alias(self, target):
        r = self.session.get(self.to_url(API_URL_IMAGE_ALIAS, {'alias': target})).json()
        if self.is_success(r):
            meta = r['metadata']
            target = meta['target']
            return self.get_image_by_id(target)

    def get_image_by_id(self, target):
        r = self.session.get(self.to_url(API_URL_IMAGE, {'image': target})).json()
        if self.is_success(r):
            return r['metadata']

    def get(self, name):
        return self.get_container_by_url(self.get_url(API_URL_CONTAINER, {'container': name}))

    def create_from_image(self, name, image, hostname=None):
        return self.create(name, {'type': "image", 'alias': image}, hostname)

    def create_from_container(self, name, source_container, hostname=None):
        return self.create(name, {'type': "copy", 'source': source_container}, hostname)

    def create(self, name, source, hostname=None, config=None, ephemeral=False):
        data = {
            'name': name,  # 64 chars max, ASCII, no slash, no colon and no comma
            'architecture': "x86_64",
            'hostname': hostname or name,
            'profiles': ["default"],  # List of profiles
            'ephemeral': ephemeral,  # Whether to destroy the container on shutdown
            'config': config,  # Config override.
            'source': source,  # Can be: "image", "migration", "copy" or "none"
            # Name of the alias
        }
        r = self.session.post(self.to_url(API_URL_CONTAINERS), data=json.dumps(data)).json()
        # print r
        error_code = 200
        if 'error_code' not in r:
            r = self.get_operation(r)
        else:
            error_code = r['error_code']
        return r, error_code

    def get_operation(self, rsp):
        retry_count = 1
        while retry_count < 10:
            r = self.session.get(self.join_url(rsp['operation'])).json()
            # print 'operation result:', r
            if self.is_success(r):
                meta = r['metadata']
                if 'Running' == meta['status']:
                    import time

                    time.sleep(2)
                    retry_count += 1
                else:
                    return meta

    def delete(self, name):
        r = self.session.delete(self.to_url(API_URL_CONTAINER, {'container': name}), data='{}').json()
        return r

    def rename(self, old_name, new_name):
        data = {
            'name': new_name
        }
        r = self.session.post(self.to_url(API_URL_CONTAINER, {'container': old_name}), data=json.dumps(data)).json()
        return r

    def start(self, name):
        return self.change_state(name, 'start')

    def stop(self, name):
        return self.change_state(name, 'stop')

    def change_state(self, name, state, sync=True):
        # State change action (stop, start, restart, freeze or unfreeze)
        param = {
            'action': state,
            'timeout': 30,
            'force': True
        }
        param = json.dumps(param)
        r = self.session.put(self.to_url(API_URL_CONTAINER_STATE, {'container': name}), data=param).json()
        if sync:
            return self.get_operation(r)
        return r

    def get_state(self, name):
        r = self.session.get(self.to_url(API_URL_CONTAINER_STATE, {'container': name})).json()
        # print r
        if self.is_success(r):
            return r['metadata']

    def image_edit(self, image, data):
        data = json.dumps(data)
        r = self.session.patch(self.to_url(API_URL_IMAGE, {'image': image}), data=data).json()
        return r

    def alias_add(self, image, added):
        for added_one in added:
            data = {
                "target": image,
                "name": added_one
            }
            r = self.session.post(self.to_url(API_URL_IMAGE_ALIASES), data=json.dumps(data)).json()
            print r

    def alias_delete(self, deleted):
        for delete_one in deleted:
            r = self.session.delete(self.to_url(API_URL_IMAGE_ALIAS, {'alias': delete_one})).json()
            print r
