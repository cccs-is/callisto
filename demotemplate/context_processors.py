import uuid
from django.conf import settings


def login_fills(request):
        return {
            'client_id': settings.CLIENT_ID,
            'redirect_uri':
                settings.DEFAULT_BASE_URL + '/complete',
            'authorize_url':
                settings.AUTHORITY_HOST_URL + '/oauth2/authorize?',
            'auth_state': settings.AUTH_STATE,
            'auth_resource': settings.OAUTH2_RESOURCE,
            'auth_scopes': settings.OAUTH2_SCOPES,
            'JH_URL': settings.JUPYTERHUB_BASE_URL,
            'base_url': request.build_absolute_uri("/").rstrip('/')
        }
