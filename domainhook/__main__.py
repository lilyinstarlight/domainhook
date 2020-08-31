import argparse
import importlib.util
import logging
import signal
import sys

import fooster.web

from domainhook import config


def main():
    parser = argparse.ArgumentParser(description='serve up a domain webhook service')
    parser.add_argument('-a', '--address', dest='address', help='address to bind')
    parser.add_argument('-p', '--port', type=int, dest='port', help='port to bind')
    parser.add_argument('-l', '--log', dest='log', help='log directory to use')
    parser.add_argument('config', help='config file to use')

    args = parser.parse_args()

    if args.address:
        config.addr = (args.address, config.addr[1])

    if args.port:
        config.addr = (config.addr[0], args.port)

    if args.log:
        if args.log == 'none':
            config.log = None
            config.http_log = None
        else:
            config.log = args.log + '/domainhook.log'
            config.http_log = args.log + '/http.log'

    config_spec = importlib.util.spec_from_file_location('config', args.config)
    config_loaded = importlib.util.module_from_spec(config_spec)
    config_spec.loader.exec_module(config_loaded)

    config.base = config_loaded.base
    if not config.base.startswith('/'):
        config.base = '/' + config.base
    if not config.base.endswith('/'):
        config.base = config.base + '/'

    if hasattr(config_loaded, 'smtp_tls'):
        config.smtp_tls = config_loaded.smtp_tls
    if hasattr(config_loaded, 'smtp_host'):
        config.smtp_host = config_loaded.smtp_host
    if hasattr(config_loaded, 'smtp_port'):
        config.smtp_port = config_loaded.smtp_port
    if hasattr(config_loaded, 'smtp_user'):
        config.smtp_user = config_loaded.smtp_user
    if hasattr(config_loaded, 'smtp_password'):
        config.smtp_password = config_loaded.smtp_password

    config.sender = config_loaded.sender
    config.recipient = config_loaded.recipient

    if hasattr(config_loaded, 'rdap_sources'):
        config.rdap_sources = config_loaded.rdap_sources

    if hasattr(config_loaded, 'dnssec_subject'):
        config.dnssec_subject = config_loaded.dnssec_subject
    if hasattr(config_loaded, 'dnssec_message'):
        config.dnssec_message = config_loaded.dnssec_message

    config.dnsimple_token = config_loaded.dnsimple_token
    config.dnsimple_webhook = config_loaded.dnsimple_webhook


    # setup logging
    log = logging.getLogger('domainhook')
    log.setLevel(logging.INFO)
    if config.log:
        log.addHandler(logging.FileHandler(config.log))
    else:
        log.addHandler(logging.StreamHandler(sys.stdout))

    if config.http_log:
        http_log_handler = logging.FileHandler(config.http_log)
        http_log_handler.setFormatter(fooster.web.HTTPLogFormatter())

        logging.getLogger('http').addHandler(http_log_handler)


    from domainhook import name, version
    from domainhook import http


    log.info(name + ' ' + version + ' starting...')

    # start everything
    http.start()


    # cleanup function
    def exit(signum, frame):
        http.stop()


    # use the function for both SIGINT and SIGTERM
    for sig in signal.SIGINT, signal.SIGTERM:
        signal.signal(sig, exit)

    # join against the HTTP server
    http.join()


if __name__ == '__main__':
    main()
