__author__ = 'kaneg'

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
