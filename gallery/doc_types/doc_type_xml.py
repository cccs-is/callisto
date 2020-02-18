from django.http import HttpResponse
from gallery.doc_types.doc_type_base import DocTypeBase
from xml.etree import ElementTree
import html


class DocTypeXML(DocTypeBase):

    @classmethod
    def doc_type(cls):
        return 'xml'

    @classmethod
    def is_my_type(cls, document_name, document_content):
        if document_name.lower().endswith('.xml'):
            return True
        try:
            root = ElementTree.fromstring(document_content)
            if root:
                return True
            return False
        except:
            return False

    @classmethod
    def export_label(cls):
        return 'Open as XML'

    @classmethod
    def importer(cls, request, document_name, document_content):
        document = super(DocTypeXML, cls).importer(request, document_name, document_content)
        return document

    @classmethod
    def exporter(cls, request, document):
        response = HttpResponse(document.document_content, content_type='text/xml')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(document.document_name)
        return response

    @classmethod
    def render(cls, request, document):
        # TODO do some form of pretty-print
        body = '<div>' + html.escape(document.document_content) + '</div>'
        return body
