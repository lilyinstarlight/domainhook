import logging

import fooster.web
import fooster.web.json

from domainhook import config, domain, notify


http = None

routes = {}
error_routes = {}


log = logging.getLogger('domainhook')


class DNSimpleWebhook(fooster.web.json.JSONHandler):
    def do_post(self):
        if self.request.body['name'] == 'dnssec.rotation_start':
            try:
                account_id, domain_id = self.request.body['account']['id'], self.request.body['data']['delegation_signer_record']['domain_id']
            except KeyError:
                raise fooster.web.HTTPError(400)

            try:
                dname = domain.get_domain(account_id, domain_id)
            except (ValueError, KeyError):
                raise fooster.web.HTTPError(404)
            except RuntimeError:
                raise fooster.web.HTTPError(500)

            try:
                domain.perform_cdscheck(dname)
            except (NameError, ValueError, KeyError):
                raise fooster.web.HTTPError(404)
            except RuntimeError:
                raise fooster.web.HTTPError(500)

            try:
                notify.send_dnssec(dname, self.request.body['data']['delegation_signer_record']['keytag'], self.request.body['data']['delegation_signer_record']['algorithm'], self.request.body['data']['delegation_signer_record']['digest_type'], self.request.body['data']['delegation_signer_record']['digest'])
            except OSError:
                log.exception('Failed to send DNSSEC key rotation notification')

        return 200, None


routes.update({'/' + config.dnsimple_webhook: DNSimpleWebhook})
error_routes.update(fooster.web.json.new_error())


def start():
    global http

    http = fooster.web.HTTPServer(config.addr, routes, error_routes)
    http.start()


def stop():
    global http

    http.stop()
    http = None


def join():
    global http

    http.join()
