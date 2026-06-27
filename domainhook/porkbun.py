import httpx

from domainhook import config


def perform_rotation(domain, dnssec_data):
    with httpx.Client(headers={'X-API-Key': config.porkbun_api_key, 'X-Secret-API-Key': config.porkbun_secret_key}) as porkbun:
        response = porkbun.get(f'https://api.porkbun.com/api/json/v3/dns/getDnssecRecords/{domain}', headers=porkbun_auth)
        if response.status_code == 400:
            raise ValueError(f'Error retrieving existing DNSSEC records from Porkbun for {domain}: {response.json()["message"]}')
        elif response.status_code != 200:
            raise RuntimeError(f'Unexpected status code {response.status_code} for domain {domain} while retrieving DNSSEC records in Porkbun')

        existing_records = response.json()['records'].keys()

        porkbun_dnssec = {
            'keyTag': dnssec_data['key_tag'],
            'alg':  dnssec_data['algorithm'],
            'digestType': dnssec_data['digest_type'],
            'digest': dnssec_data['digest'],
            'keyDataFlags': dnssec_data['key_data_flags'],
            'keyDataProtocol': dnssec_data['key_data_protocol'],
            'keyDataAlgo': dnssec_data['key_data_algorithm'],
            'keyDataPubKey': dnssec_data['key_data_public_key'],
        }

        response = porkbun.post(f'https://api.porkbun.com/api/json/v3/dns/createDnssecRecord/{domain}', headers=porkbun_auth, data=json.dumps(porkbun_dnssec))
        if response.status_code == 400:
            raise ValueError(f'Error creating DNSSEC record with key tag {dnssec_data["key_tag"]} in Porkbun for {domain}: {response.json()["message"]}')
        elif response.status_code != 200:
            raise RuntimeError(f'Unexpected status code {response.status_code} for domain {domain} while creating DNSSEC record with key tag {dnssec_data["key_tag"]} in Porkbun')

        for key_tag in existing_records.keys():
            if key_tag == dnssec_data['key_tag']:
                continue

            response = porkbun.post(f'https://api.porkbun.com/api/json/v3/dns/deleteDnssecRecord/{domain}/{key_tag}', headers=porkbun_auth)
            if response.status_code == 400:
                raise ValueError(f'Error removing DNSSEC record with key tag {key_tag} in Porkbun for {domain}: {response.json()["message"]}')
            elif response.status_code != 200:
                raise RuntimeError(f'Unexpected status code {response.status_code} for domain {domain} while remove DNSSEC record with key tag {key_tag} in Porkbun')
