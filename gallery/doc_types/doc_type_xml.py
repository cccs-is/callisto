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
    def _convert(cls, elem, level=0):
        safe_tag = html.escape(elem.tag)
        safe_text = html.escape(elem.text) if elem.text else None
        safe_tail = html.escape(elem.tail) if elem.tail else None
        has_children = (len(elem) > 0)

        indent = ' style="text-indent: {0}px;"'.format(level * 25) if level else ''

        result = '<p ' + indent + '>'
        result += level * '  '
        result += '&lt;' + '<span class="xml-tag">' + safe_tag + '</span>'
        for name, value in elem.attrib.items():
            result += ' ' + '<span class="xml-attr-name">' + html.escape(name) + '</span>' + '=&quot;' + '<span class="xml-attr-value">' + html.escape(value) + '</span>' + '&quot;'
        result += '&gt;'

        if safe_text:
            result += safe_text
        if has_children:
            result += "</p>"
            for child in elem:
                result += cls._convert(child, level + 1)
            result += '<p ' + indent + '>'
        if safe_tail:
            result += safe_tail
        result += '&lt;/' + '<span class="xml-tag">' + safe_tag + '</span>' + '&gt;</p>'
        return result

    @classmethod
    def render(cls, request, document):
        root = ElementTree.fromstring(document.document_content)
        return cls._convert(root)
