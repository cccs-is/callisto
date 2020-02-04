from django.contrib.auth.decorators import login_required
from .models import SharedNotebook, NotebookLike
from django.shortcuts import render, redirect
import nbconvert
import nbformat
from django.urls import reverse
from django.http import HttpResponse
import arrow
import requests
from django.conf import settings


# This is the cookie name used by OAuth2 proxy
# By default it is '_oauth2_proxy' and can be changed using '-cookie-name' config on the OAuth2 proxy.
OAUTH_COOKIE_NAME = '_oauth2_proxy'


@login_required
def notebook_details(request, notebook_id):
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    nbview_session_key = 'nb-view-{}'.format(notebook_id)
    if not request.session.get(nbview_session_key):
        request.session[nbview_session_key] = True
        notebook.views += 1
        notebook.save()

    if notebook.master_notebook:
        other_notebooks = notebook.master_notebook.sharednotebook_set.exclude(pk=notebook.id)
    else:
        other_notebooks = notebook.sharednotebook_set.exclude(pk=notebook.id)

    liked = False
    hub_member = request.user
    if notebook.notebooklike_set.filter(hub_member=hub_member):
        liked = True

    format_notebook = nbformat.reads(notebook.notebook_content, as_version=nbformat.NO_CONVERT)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    # below also removes output of code
    # html_exporter.exclude_code_cell = True

    (body, resources) = html_exporter.from_notebook_node(format_notebook)
    context = {'notebook': notebook,
               'other_notebooks': other_notebooks,
               'notebook_preview': body,
               'liked': liked}
    return render(request, 'gallery/notebook_details.html', context=context)


@login_required
def like_notebook(request, notebook_id):
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    hub_member = request.user
    if notebook.notebooklike_set.filter(hub_member=hub_member):
        like = NotebookLike.objects.get(hub_member=hub_member, notebook=notebook)
        like.delete()
    else:
        like = NotebookLike(notebook=notebook, hub_member=hub_member, created_at=arrow.now().format())
        like.save()
    return redirect(reverse('notebook-details', args=(notebook_id,)))


def render_notebook(request, notebook_id):
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    format_notebook = nbformat.reads(notebook.notebook_content, as_version=nbformat.NO_CONVERT)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    # below also removes output of code
    # html_exporter.exclude_code_cell = True
    (body, resources) = html_exporter.from_notebook_node(format_notebook)
    return HttpResponse(body)


@login_required
def open_notebook_hub(request, notebook_id):
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    nbview_session_key = 'nb-view-{}'.format(notebook_id)
    if not request.session.get(nbview_session_key):
        request.session[nbview_session_key] = True
        notebook.views += 1
        notebook.save()

    # payload: notebook contents, notebook name
    data = {'notebook_name': notebook.notebook_name, 'notebook_contents': notebook.notebook_content}
    # authentication:
    access_token = request.headers.get('X-Access-Token')
    if access_token:
        headers = {'Authorization': 'Bearer ' + access_token}
    else:
        headers = {}
    oauth_cookies = None
    if request.COOKIES.get(OAUTH_COOKIE_NAME) is not None:
        oauth_cookies = {OAUTH_COOKIE_NAME: request.COOKIES.get(OAUTH_COOKIE_NAME)}
    # URL to call :
    # This must matches processing done by the JupyterHub authenticator to convert external 'unique_name'
    # into the name used by the Hub:
    unique_name = request.user.email
    jhub_user_name = unique_name.split('@')[0].replace('.', '-')
    jhub_user_url = settings.JUPYTERHUB_URL.rstrip('/') + '/user/' + jhub_user_name

    post_url = jhub_user_url + '/notebook-import'
    print('Sending notebook to: ' + str(post_url))
    response = requests.post(url=post_url, headers=headers, cookies=oauth_cookies, json=data, timeout=60.0)

    if response.status_code == 200:
        response_data = response.json()
        actual_notebook_name = response_data.get('notebook_name')
        redirect_url = jhub_user_url + '/notebooks/' + actual_notebook_name
        return redirect(redirect_url)

    return HttpResponse('Upload failed. Jupyter Hub returned code: {0} with message {1}'.
                        format(response.status_code, response.text), status=response.status_code)
