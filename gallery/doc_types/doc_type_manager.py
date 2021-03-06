import html
from gallery.doc_types.doc_type_notebook import DocTypeNotebook
from gallery.doc_types.doc_type_xml import DocTypeXML


class DocTypeManager:
    """
    Directs generic document requests to specific doc types
    """

    # Map DocTypeName -> Implementation
    ALL_DOC_TYPES = {
        DocTypeNotebook.doc_type(): DocTypeNotebook(),
        DocTypeXML.doc_type(): DocTypeXML()
    }

    def available_doc_types(self):
        return self.ALL_DOC_TYPES.keys()

    def doc_type(self, document_name, document_content):
        for key, doc_type_impl in self.ALL_DOC_TYPES.items():
            if doc_type_impl.is_my_type(document_name, document_content):
                return key
        return None

    def export_label(self, document):
        doc_type_impl = self.ALL_DOC_TYPES.get(document.document_type)
        return doc_type_impl.export_label()

    def importer(self, request, document_type, document_name, document_content):
        doc_type_impl = self.ALL_DOC_TYPES.get(document_type)
        return doc_type_impl.importer(request, document_name, document_content)

    def exporter(self, request, document):
        doc_type_impl = self.ALL_DOC_TYPES.get(document.document_type)
        return doc_type_impl.exporter(request, document)

    def render(self, request, document):
        doc_type_impl = self.ALL_DOC_TYPES.get(document.document_type)
        try:
            return doc_type_impl.render(request, document)
        except Exception as e:
            error_message = html.escape(str(e))
            doc_type = doc_type_impl.doc_type()
            return '<div><p>Unable to render as {0}:</p> <p>{1}</p> </div>'.format(doc_type, error_message)


doc_type_manager = DocTypeManager()
