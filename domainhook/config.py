import json as _json
import logging as _logging
import os as _os
import sys as _sys

import fooster.web as _web


# address to listen on
addr = ('', 8000)

# directory to store information
dir = '/var/lib/domainhook'

# log locations
log = '/var/log/domainhook/domainhook.log'
http_log = '/var/log/domainhook/http.log'

# expire time delta
expire = 604800  # 7 days

# URL base path
base = '/'

# notification
smtp_tls = None  # None, 'starttls', 'tls'
smtp_host = 'localhost'
smtp_port = 0
smtp_user = ''
smtp_password = ''

sender = 'noreply@example.com'
recipient = 'hostmaster@example.com'

dnssec_subject = 'DNSSEC Key Rotated for {domain}'
dnssec_message = '''
Rotated key at registrar for {domain}. New key:

{domain} IN DS {keytag} {algorithm} {digest_type} {digest}
'''

failure_subject = 'Webhook Failure for {domain}'
failure_message = '''
Webhook {action} failed for {domain}:

{message}
'''

# rdap sources
rdap_sources = {
    '_': 'rdap.org',
}

# dnsimple integration
dnsimple_token = '0123456789abcdefghijklmnopqrstuv'
dnsimple_webhook = 'dnsimple'


# store config in env var
def _store():
    config = {key: val for key, val in globals().items() if not key.startswith('_')}

    _os.environ['DOMAINHOOK_CONFIG'] = _json.dumps(config)


# load config from env var
def _load():
    config = _json.loads(_os.environ['DOMAINHOOK_CONFIG'])

    globals().update(config)

    # automatically apply
    _apply()


# apply special config-specific logic after changes
def _apply():
    # setup logging
    if log:
        _logging.getLogger('domainhook').addHandler(_logging.FileHandler(log))
    else:
        _logging.getLogger('domainhook').addHandler(_logging.StreamHandler(_sys.stdout))

    _logging.getLogger('domainhook').setLevel(_logging.INFO)

    if http_log:
        http_log_handler = _logging.FileHandler(http_log)
        http_log_handler.setFormatter(_web.HTTPLogFormatter())

        _logging.getLogger('http').addHandler(http_log_handler)

    # automatically store if not already serialized
    if 'DOMAINHOOK_CONFIG' not in _os.environ:
        _store()


# load if config already serialized in env var
if 'DOMAINHOOK_CONFIG' in _os.environ:
    _load()
