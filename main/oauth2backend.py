import jwt
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied


class OAuth2Authentication:
    """
    Token-based authentication backend.
    The backend assumes that the actual authentication and user management is done by some other actor (such as
    a reverse proxy) which passes in OAuth2 token in the 'Authorization' header, using type AUTHORIZATION_TYPE.
    At this time code is somewhat specific to Azure as it needs to get Azure public certificate to verify
    token's signature.
    """
    AUTHORIZATION_TYPE = 'Bearer '

    def azure_public_certificate(self, user_token):
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

    def verify_and_decode(self, user_token):
        cert_str = self.azure_public_certificate(user_token)
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

    def authenticate(self, request):
        access_token = request.headers.get('Authorization')
        if not access_token:
            return None
        if access_token.startswith(self.AUTHORIZATION_TYPE):
            access_token = access_token[len(self.AUTHORIZATION_TYPE):]

        decoded = self.verify_and_decode(access_token)
        if not decoded:
            return None

        user_id = decoded.get('oid')
        try:
            user = User.objects.get(username=user_id)
            print('Found user: ', user.first_name, ' ', user.last_name )
            if not user.is_active:
                raise PermissionDenied()
        except User.DoesNotExist:
            user = User(username=user_id)
            user.first_name =  decoded.get('given_name')
            user.last_name = decoded.get('family_name')
            user.email = decoded.get('unique_name') # TODO check if with proper scope we can get e-mail claim
            print('Creating user: ', user.first_name, ' ', user.last_name )
            user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
