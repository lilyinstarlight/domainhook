import collections.abc
import logging

import fooster.web
import fooster.web.json

from domainhook import config, domain, notify, porkbun, request


http = None

routes = {}
error_routes = {}


log = logging.getLogger('domainhook')


class DNSimpleWebhook(fooster.web.json.JSONHandler):
    def do_post(self):
        if not isinstance(self.request.body, collections.abc.Mapping) or 'request_identifier' not in self.request.body or 'name' not in self.request.body:
            raise fooster.web.HTTPError(400)

        if request.exists(self.request.body['request_identifier']):
            return 200, None

        if self.request.body['name'] == 'dnssec.rotation_start':
            try:
                account_id, domain_id = self.request.body['account']['id'], self.request.body['data']['zone']['id']

                dnssec_data = {
                    'key_tag': self.request.body['data']['delegation_signer_record']['keytag'],
                    'algorithm': self.request.body['data']['delegation_signer_record']['algorithm'],
                    'digest_type': self.request.body['data']['delegation_signer_record']['digest_type'],
                    'digest': self.request.body['data']['delegation_signer_record']['digest'],
                    'key_data_flags': 257,
                    'key_data_protocol': 3,
                    'key_data_algorithm': self.request.body['data']['delegation_signer_record']['algorithm'],
                    'key_data_public_key': self.request.body['data']['delegation_signer_record']['public_key'],
                }
            except KeyError:
                raise fooster.web.HTTPError(400)

            try:
                dname = domain.get_domain(account_id, domain_id)
            except (ValueError, KeyError):
                log.exception('Failure performing domain lookup')
                raise fooster.web.HTTPError(404)
            except RuntimeError:
                log.exception('Error performing domain lookup')
                raise fooster.web.HTTPError(500)

            if config.porkbun_api_key and config.porkbun_secret_key:
                try:
                    porkbun.perform_rotation(dname, dnssec_data)
                except (NameError, ValueError, KeyError) as err:
                    log.exception('Failure performing Porkbun rotation')
                    try:
                        notify.send_failure(dname, self.request.body['name'], str(err))
                    except OSError:
                        log.exception('Failed to send failure notification')
                    raise fooster.web.HTTPError(404)
                except RuntimeError as err:
                    log.exception('Error performing Porkbun rotation')
                    try:
                        notify.send_failure(dname, self.request.body['name'], str(err))
                    except OSError:
                        log.exception('Failed to send failure notification')
                    raise fooster.web.HTTPError(500)
            else:
                try:
                    domain.perform_cdscheck(dname)
                except (NameError, ValueError, KeyError) as err:
                    log.exception('Failure performing CDS check')
                    try:
                        notify.send_failure(dname, self.request.body['name'], str(err))
                    except OSError:
                        log.exception('Failed to send failure notification')
                    raise fooster.web.HTTPError(404)
                except RuntimeError as err:
                    log.exception('Error performing CDS check')
                    try:
                        notify.send_failure(dname, self.request.body['name'], str(err))
                    except OSError:
                        log.exception('Failed to send failure notification')
                    raise fooster.web.HTTPError(500)

            try:
                notify.send_dnssec(dname, dnssec_data)
            except OSError:
                log.exception('Failed to send DNSSEC key rotation notification')

        request.add(self.request.body['request_identifier'])

        return 200, None


routes.update({config.base + config.dnsimple_webhook: DNSimpleWebhook})
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
