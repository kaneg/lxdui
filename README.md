# LXD UI
Web UI for LXD

# Requirement
* Flask: pip install flask
* Gotty: https://github.com/yudai/gotty
# Usage
```python main.py```

# Configuration
### 1. Settings
In settings.py, you can change below settings:

```python
server_host = '0.0.0.0'
server_port = 8080
debug = False

lxd_api_url = 'unix:/var/lib/lxd/unix.socket'
ssl_key_path = '~/.config/lxc/client.key'
ssl_crt_path = '~/.config/lxc/client.crt'
web_shell_host = 'http://%(host)s:9090/?arg=%(container)s'
login_required = True
admin_user = 'admin'
admin_password = 'admin'
```

### 2. Users:
Create a json file under the root folder, named it to users.json based on the template users.tpl.json.
In the json file, you can add users with password and different permissions.
