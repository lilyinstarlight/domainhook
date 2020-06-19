import logging

import httpx

from domainhook import config


log = logging.getLogger('domainhook')


def get_domain(account_id, domain_id):
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {config.dnsimple_token}',
    }
    response = httpx.get(f'https://api.dnsimple.com/v2/{account_id}/domains/{domain_id}', headers=headers)

    if response.status_code == 401:
        log.error(f'Authorization failed for domain {domain_id} on account {account_id}')
        raise ValueError()
    elif response.status_code == 404:
        log.error(f'Domain {domain_id} on account {account_id} not found')
        raise KeyError()
    elif response.status_code != 200:
        log.error(f'Unexpected status code {response.status_code} for domain {domain_id} on account {account_id}')
        raise RuntimeError()

    return response.json()['data']['name']


def perform_cdscheck(domain):
    cdscheck = None
    rdaps = []

    rdap_source = config.rdap_sources.get(domain.rpartition('.')[2], config.rdap_sources['_'])

    response = httpx.get(f'https://{rdap_source}/domain/{domain}')
    if response.status_code == 404:
        log.error(f'Could not find domain {domain} in RDAP')
        raise NameError()
    elif response.status_code != 200:
        log.error(f'Unexpected status code {response.status_code} for domain {domain} in RDAP')
        raise RuntimeError()
    rdaps.append(response.json())

    for link in rdaps[-1]['links']:
        if link['rel'] == 'https://rdap.io/tpda/cdscheck':
            cdscheck = link['href']
            break

    if not cdscheck:
        related = None

        for link in rdaps[-1]['links']:
            if link['rel'] == 'related':
                related = link['href']
                break

        if related:
            response = httpx.get(related)
            if response.status_code == 404:
                log.error(f'Domain not found at related RDAP URL {related}')
                raise NameError()
            elif response.status_code != 200:
                log.error(f'Unexpected status code {response.status_code} at related RDAP URL {related}')
                raise RuntimeError()
            rdaps.append(response.json())

            for link in rdaps[-1]['links']:
                if link['rel'] == 'https://rdap.io/tpda/cdscheck':
                    cdscheck = link['href']
                    break

    if not cdscheck:
        log.error(f'Could not find cdscheck URL in RDAP for domain {domain}')
        raise NameError()

    response = httpx.put(cdscheck)

    if response.status_code == 401:
        log.error(f'Unauthorized at cdscheck URL {cdscheck}')
        raise ValueError()
    elif response.status_code == 404:
        log.error(f'Domain not found at cdscheck URL {cdscheck}')
        raise KeyError()
    elif response.status_code != 200:
        log.error(f'Unexpected status code {response.status_code} at cdscheck URL {cdscheck}')
        raise RuntimeError()
