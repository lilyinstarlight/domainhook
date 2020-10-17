import httpx

from domainhook import config


def get_domain(account_id, domain_id):
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {config.dnsimple_token}',
    }
    response = httpx.get(f'https://api.dnsimple.com/v2/{account_id}/domains/{domain_id}', headers=headers)

    if response.status_code == 401:
        raise ValueError(f'Authorization failed for domain {domain_id} on account {account_id}')
    elif response.status_code == 404:
        raise KeyError(f'Domain {domain_id} on account {account_id} not found')
    elif response.status_code != 200:
        raise RuntimeError(f'Unexpected status code {response.status_code} for domain {domain_id} on account {account_id}')

    return response.json()['data']['name']


def perform_cdscheck(domain):
    cdscheck = None
    rdaps = []

    rdap_source = config.rdap_sources.get(domain.rpartition('.')[2], config.rdap_sources['_'])

    response = httpx.get(f'https://{rdap_source}/domain/{domain}')
    if response.status_code == 404:
        raise NameError(f'Could not find domain {domain} in RDAP')
    elif response.status_code != 200:
        raise RuntimeError(f'Unexpected status code {response.status_code} for domain {domain} in RDAP')
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
                raise NameError(f'Domain not found at related RDAP URL {related}')
            elif response.status_code != 200:
                raise RuntimeError(f'Unexpected status code {response.status_code} at related RDAP URL {related}')
            rdaps.append(response.json())

            for link in rdaps[-1]['links']:
                if link['rel'] == 'https://rdap.io/tpda/cdscheck':
                    cdscheck = link['href']
                    break

    if not cdscheck:
        raise NameError(f'Could not find cdscheck URL in RDAP for domain {domain}')

    response = httpx.put(cdscheck)

    if response.status_code == 401:
        raise ValueError(f'Unauthorized at cdscheck URL {cdscheck}')
    elif response.status_code == 404:
        raise KeyError(f'Domain not found at cdscheck URL {cdscheck}')
    elif response.status_code != 200:
        raise RuntimeError(f'Unexpected status code {response.status_code} at cdscheck URL {cdscheck}')
