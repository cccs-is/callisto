#!/usr/bin/env python

import os
import jwt
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend


def azure_public_certificate(user_token):
    token_header = jwt.get_unverified_header(user_token)
    token_kid = token_header.get('kid')
    token_x5t = token_header.get('x5t')

    azure_reply = requests.get(url='https://login.microsoftonline.com/common/discovery/keys', timeout=3.0)
    azure_data = azure_reply.json()
    for key in azure_data.get('keys'):
        if key.get('kid') == token_kid and key.get('x5t') == token_x5t:
            cert_body = key.get('x5c')[0]
            return '-----BEGIN CERTIFICATE-----\n' + cert_body + '\n-----END CERTIFICATE-----\n'
    return None


def verify_and_decode(user_token):
    cert_str = azure_public_certificate(user_token)
    cert_obj = load_pem_x509_certificate(cert_str.encode('utf-8'), default_backend())
    public_key = cert_obj.public_key()

    # This is not correct and should be fixed in the login sequence.
    # The proper value should be == TENANT
    tenant_id = 'https://graph.windows.net'
    # Proper way once login proxy is fixed:
    # tenant_id = os.getenv('TENANT', '')

    try:
        return jwt.decode(user_token, public_key, algorithms=['RS256'], audience=tenant_id)
    except jwt.exceptions.InvalidTokenError as e:
        print('Exception: ' + repr(e))
    return None
