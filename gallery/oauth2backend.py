import jwt
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings


class OAuth2Authentication:
    """
    Token-based authentication backend.
    The backend assumes that the actual authentication and user management is done by some other actor (such as
    a reverse proxy) which passes in OAuth2 token in the 'Authorization' header, using type AUTHORIZATION_TYPE.

    The flow is tested with Azure Active Domain as OAuth2 provider. Other OAuth providers might need code adjustment
    if they supply public signatures using different paradigm.
    """
    AUTHORIZATION_TYPE = 'Bearer '

    def oauth_provider_public_certificate(self, user_token):
        """
        The method expects to get list of keys used by matching 'kid' and 'x5t' token claims
        from a well-known URL supplied by the OAuth provider.
        The keys are then wrapped to form standard public certificate.
        """
        token_header = jwt.get_unverified_header(user_token)
        token_kid = token_header.get('kid')
        token_x5t = token_header.get('x5t')

        url = settings.OAUTH_PUBLIC_KEYS_URL
        reply = requests.get(url=url, timeout=10.0)
        reply_data = reply.json()
        for key in reply_data.get('keys'):
            if key.get('kid') == token_kid and key.get('x5t') == token_x5t:
                cert_body = key.get('x5c')[0]
                return '-----BEGIN CERTIFICATE-----\n' + cert_body + '\n-----END CERTIFICATE-----\n'
        return None

    def verify_and_decode(self, user_token):
        cert_str = self.oauth_provider_public_certificate(user_token)
        cert_obj = load_pem_x509_certificate(cert_str.encode('utf-8'), default_backend())
        public_key = cert_obj.public_key()
        audience = settings.OAUTH_TOKEN_AUDIENCE
        try:
            return jwt.decode(user_token, public_key, algorithms=['RS256'], audience=audience)
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
