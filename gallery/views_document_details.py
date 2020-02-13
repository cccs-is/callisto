from django.contrib.auth.decorators import login_required
from .models import SharedDocument, DocumentLike
from django.shortcuts import render, redirect
import nbconvert
import nbformat
from django.urls import reverse
from django.http import HttpResponse
import arrow
import requests
from django.conf import settings
from django.contrib import messages


# This is the cookie name used by OAuth2 proxy
# By default it is '_oauth2_proxy' and can be changed using '-cookie-name' config on the OAuth2 proxy.
OAUTH_COOKIE_NAME = '_oauth2_proxy'


@login_required
def document_details(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)

    if not document.can_read(request.user):
        messages.warning(request, 'Permission denied!')
        return redirect("/")

    nbview_session_key = 'nb-view-{}'.format(document_id)
    if not request.session.get(nbview_session_key):
        request.session[nbview_session_key] = True
        document.views += 1
        document.save()

    if document.master_document:
        other_documents = document.master_document.shareddocument_set.exclude(pk=document.id)
    else:
        other_documents = document.shareddocument_set.exclude(pk=document.id)

    liked = False
    hub_member = request.user
    if document.documentlike_set.filter(hub_member=hub_member):
        liked = True


    # FIXME below is document-speific portion, to be extracted into DocType
    format_notebook = nbformat.reads(document.document_content, as_version=nbformat.NO_CONVERT)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    # below also removes output of code
    # html_exporter.exclude_code_cell = True

    (body, resources) = html_exporter.from_notebook_node(format_notebook)
    context = {'document': document,
               'other_documents': other_documents,
               'document_preview': body,
               'liked': liked}
    return render(request, 'gallery/document_details.html', context=context)


@login_required
def like_document(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)
    hub_member = request.user
    if document.documentlike_set.filter(hub_member=hub_member):
        like = DocumentLike.objects.get(hub_member=hub_member, document=document)
        like.delete()
    else:
        like = DocumentLike(document=document, hub_member=hub_member, created_at=arrow.now().format())
        like.save()
    return redirect(reverse('document-details', args=(document_id,)))


def render_document(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)

    # FIXME document-specific, extract into DocType
    format_notebook = nbformat.reads(document.document_content, as_version=nbformat.NO_CONVERT)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    # below also removes output of code
    # html_exporter.exclude_code_cell = True
    (body, resources) = html_exporter.from_notebook_node(format_notebook)
    return HttpResponse(body)


@login_required
def open_document_hub(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)
    nbview_session_key = 'nb-view-{}'.format(document_id)
    if not request.session.get(nbview_session_key):
        request.session[nbview_session_key] = True
        document.views += 1
        document.save()


    # payload: document contents, document name
    # FIXME document_name -> document_name, notebook_contents -> document_contents
    data = {'document_name': document.document_name, 'notebook_contents': document.document_content}
    # authentication:
    access_token = request.headers.get('X-Access-Token')
    if access_token:
        headers = {'Authorization': 'Bearer ' + access_token}
    else:
        headers = {}
    oauth_cookies = None
    if request.COOKIES.get(OAUTH_COOKIE_NAME) is not None:
        oauth_cookies = {OAUTH_COOKIE_NAME: request.COOKIES.get(OAUTH_COOKIE_NAME)}

    # FIXME below is Jupyter Hub specific code, extract into DocType
    # URL to call :
    # This must matches processing done by the JupyterHub authenticator to convert external 'unique_name'
    # into the name used by the Hub:
    unique_name = request.user.email
    jhub_user_name = unique_name.split('@')[0].replace('.', '-')
    jhub_user_url = settings.JUPYTERHUB_URL.rstrip('/') + '/user/' + jhub_user_name

    post_url = jhub_user_url + '/document-import'
    response = requests.post(url=post_url, headers=headers, cookies=oauth_cookies, json=data, timeout=60.0)

    if response.status_code == 200:
        response_data = response.json()
        actual_document_name = response_data.get('document_name')
        redirect_url = jhub_user_url + '/documents/' + actual_document_name
        return redirect(redirect_url)

    return HttpResponse('Upload failed. Jupyter Hub returned code: {0} with message {1}'.
                        format(response.status_code, response.text), status=response.status_code)
