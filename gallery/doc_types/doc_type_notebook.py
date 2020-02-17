import json
import requests
import nbconvert
import nbformat
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from gallery.doc_types.doc_type_base import DocTypeBase


class DocTypeNotebook(DocTypeBase):

    @classmethod
    def doc_type(cls):
        return 'notebook'

    @classmethod
    def is_my_type(cls, document_name, document_content):
        if document_name.lower().endswith('.ipynb'):
            return True
        try:
            contents = json.loads(document_content)
        except:
            return False
        cells = contents.get('cells')
        if cells:
            return True
        return False

    @classmethod
    def export_label(cls):
        return 'Open in JupyterHub'

    @classmethod
    def importer(cls, request, document_name, document_content):
        document = super(DocTypeNotebook, cls).importer(request, document_name, document_content)
        return document

    @classmethod
    def exporter(cls, request, document):
        # payload: document contents, document name
        # FIXME notebook_name -> document_name, notebook_contents -> document_contents
        data = {'notebook_name': document.document_name, 'notebook_contents': document.document_content}
        # URL to call :
        # This must matches processing done by the JupyterHub authenticator to convert external 'unique_name'
        # into the name used by the Hub:
        unique_name = request.user.email
        jhub_user_name = unique_name.split('@')[0].replace('.', '-')
        jhub_user_url = settings.JUPYTERHUB_URL.rstrip('/') + '/user/' + jhub_user_name

        post_url = jhub_user_url + '/document-import'
        headers = cls._oauth_header(request)
        oauth_cookies = cls._oauth_header(request)
        response = requests.post(url=post_url, headers=headers, cookies=oauth_cookies, json=data, timeout=60.0)

        if response.status_code == 200:
            response_data = response.json()
            actual_document_name = response_data.get('document_name')
            redirect_url = jhub_user_url + '/documents/' + actual_document_name
            return redirect(redirect_url)

        return HttpResponse('Upload failed. Jupyter Hub returned code: {0} with message {1}'.
                            format(response.status_code, response.text), status=response.status_code)

    @classmethod
    def render(cls, request, document):
        format_notebook = nbformat.reads(document.document_content, as_version=nbformat.NO_CONVERT)
        html_exporter = nbconvert.HTMLExporter()
        html_exporter.template_file = 'basic'
        # below also removes output of code
        # html_exporter.exclude_code_cell = True
        (body, resources) = html_exporter.from_notebook_node(format_notebook)
        return body
