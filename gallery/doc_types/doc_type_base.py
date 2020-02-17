from abc import abstractmethod, ABCMeta

from gallery.helpers import identify_master_document

import arrow
from gallery.models import SharedDocument
from django.contrib import messages


class DocTypeBase(metaclass=ABCMeta):
    """
    All methods on DocTypes must be implemented in a thread-safe way.
    """

    # This is the cookie name used by OAuth2 proxy
    # By default it is '_oauth2_proxy' and can be changed using '-cookie-name' config on the OAuth2 proxy.
    OAUTH_COOKIE_NAME = '_oauth2_proxy'

    @classmethod
    def _oauth_cookies(cls, request):
        if request.COOKIES.get(cls.OAUTH_COOKIE_NAME) is not None:
            return {cls.OAUTH_COOKIE_NAME: request.COOKIES.get(cls.OAUTH_COOKIE_NAME)}
        return None

    @classmethod
    def _oauth_header(cls, request):
        access_token = request.headers.get('X-Access-Token')
        if access_token:
            return {'Authorization': 'Bearer ' + access_token}
        return {}

    @classmethod
    def export_label(cls):
        """
        Returns label similar to "Open As..." for this document type
        """
        return 'Open'

    @classmethod
    @abstractmethod
    def doc_type(cls):
        pass

    @classmethod
    @abstractmethod
    def is_my_type(cls, document_name, document_content):
        pass

    @classmethod
    def importer(cls, request, document_name, document_content):
        hub_member = request.user
        document, created = SharedDocument.objects.get_or_create(hub_member=hub_member, document_name=document_name)
        document.document_content = document_content
        document.document_name = document_name
        document.updated_at = arrow.now().format()
        document.hub_member = hub_member
        document.master_document = identify_master_document(document_name, hub_member)
        document.tags = '{}'
        document.data_sources = '{}'
        document.document_type = cls.doc_type()
        if created:
            document.created_at = arrow.now().format()
            messages.info(request, 'Your document {} has been uploaded!'.format(document_name))
        else:
            messages.info(request, 'Your document {} has been updated!'.format(document_name))
        document.save()
        return document

    @classmethod
    @abstractmethod
    def exporter(cls, request, document):
        """
        Returns HttpResponse resulting from exporting the document.
        """
        pass

    @classmethod
    @abstractmethod
    def render(cls, request, document):
        """
        Returns HTTP <div> rendering the document
        """
        pass
