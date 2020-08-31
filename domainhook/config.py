# address to listen on
addr = ('', 8000)

# log locations
log = '/var/log/domainhook/domainhook.log'
http_log = '/var/log/domainhook/http.log'

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

# rdap sources
rdap_sources = {
    '_': 'rdap.org',
}

# dnsimple integration
dnsimple_token = '0123456789abcdefghijklmnopqrstuv'
dnsimple_webhook = 'dnsimple'
