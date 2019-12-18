import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.conf import settings
from ohapi import api
from .helpers import get_notebook_files, get_notebook_oh, download_notebook_oh
from .helpers import find_notebook_by_keywords, get_all_data_sources
from .helpers import suggest_data_sources, add_notebook_helper, add_notebook_direct
from .helpers import paginate_items, oh_code_to_member
from .helpers import get_all_data_sources_numeric
from .models import SharedNotebook
import arrow
import json
import requests_oauthlib
import jwt
import uuid
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .oauth_utils import verify_and_decode

# OAuth token prefix passed in the REST header
AUTHORIZATION_TYPE = 'Bearer '

# Set up logging.
logger = logging.getLogger(__name__)
MSGRAPH = requests_oauthlib.OAuth2Session(settings.CLIENT_ID,
                                    scope=settings.OAUTH2_SCOPES,
                                    redirect_uri=settings.REDIRECT_URI)

@login_required(login_url="/")
def shared(request):
    """
    Users get linked here after clicking export
    on notebooks.openhumans.org
    """
    access_token = request.META.get('HTTP_X_ACCESS_TOKEN', None)
    if request.user.is_authenticated:
        print('in shared()-> user:', request.user)
        messages.info(request,
                      ("Your notebook was uploaded into your Open Humans "
                       "account and can now be shared from here!"))
        return redirect('/dashboard')
    elif access_token != None:
        # TBD: we need to verify the token 
        access_info = jwt.decode(access_token, verify=False)
        print('>>> access_info:', access_info)
        data = {'access_token': access_token,
                'expires_in': access_info['exp'], 
                'refresh_token': '', #tokens['refresh_token'],
                'id': access_info['oid'],
                'username': access_info['unique_name']
                }

        oh_member = oh_code_to_member(data)

        if oh_member:
            # Log in the user.
            user = oh_member.user
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')

    latest_notebooks = SharedNotebook.objects.all(
        ).order_by('-updated_at')[:10]
    print('in shared()-> lates_notebooks:', latest_notebooks)
    context = {'latest_notebooks': latest_notebooks}
    return render(request, 'main/shared.html', context)


def index(request):
    """
    Starting page for app.
    """
    #print('>>> request.META:', request.META)
    access_token = request.META.get('HTTP_X_ACCESS_TOKEN', None)

    if request.user.is_authenticated:
        print('index() - request.user:', request.user)
        return redirect('/notebooks')
    elif access_token != None:
        # TBD: we need to verify the token 
        access_info = jwt.decode(access_token, verify=False)
        print('>>> access_info:', access_info)
        data = {'access_token': access_token,
                'expires_in': access_info['exp'], 
                'refresh_token': '', #tokens['refresh_token'],
                'id': access_info['oid'],
                'username': access_info['unique_name']
                }

        oh_member = oh_code_to_member(data)

        if oh_member:
            # Log in the user.
            user = oh_member.user
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            return redirect("/dashboard")

    # otherwise
    latest_notebooks = SharedNotebook.objects.filter(
            master_notebook=None).order_by('-views')[:5]
    data_sources = get_all_data_sources()[:6]
    context = {'oh_proj_page': settings.OH_ACTIVITY_PAGE,
                   'latest_notebooks': latest_notebooks,
                   'data_sources': data_sources}

    return render(request, 'main/index.html', context=context)


def data_source_index(request):
    data_sources = get_all_data_sources_numeric()
    return render(request, 'main/sources_index.html', {
                'section': 'sources',
                'data_sources': data_sources})


def about(request):
    return render(request, 'main/about.html', {'section': 'about'})


@login_required(login_url="/")
def delete_user(request):
    if request.method == "POST":
        request.user.delete()
        messages.info(request, "Your account was deleted!")
        logout(request)
    return redirect('index')

def login_user(request):
    # print('Attempt to login to MSFT!!!')
    auth_base = settings.AUTHORITY_HOST_URL + '/oauth2/v2.0/authorize'
    authorization_url, state = MSGRAPH.authorization_url(auth_base)
    MSGRAPH.auth_state = state
    return redirect(authorization_url)

def complete(request):
    """
    Receive user from Open Humans. Store data, start upload.
    """
 
    # Exchange code for token.
    # This creates an OpenHumansMember and associated user account.
    code = request.GET.get('code', '')
    tokens = MSGRAPH.fetch_token(settings.AUTHORITY_HOST_URL + '/oauth2/v2.0/token',
                    client_secret=settings.CLIENT_SECRET,
                    code = code)
    
    access_info = jwt.decode(tokens['access_token'], verify=False)
    # print('ACCESS_INFO:', access_info)

    # endpoint = settings.OAUTH2_RESOURCE + '/v1.0/me'
    # headers = {'SdkVersion': 'juno-0.1.0',
    #         'x-client-SKU': 'juno',
    #         'client-request-id': str(uuid.uuid4()),
    #         'return-client-request-id': 'true'}
    # graphdata = MSGRAPH.get(endpoint, headers=headers).json()
    # print('>>> MSGraph res:', graphdata)

    # print('>>> tokens keys:', tokens.keys())

    data = {'access_token': tokens['access_token'],
            'expires_in': tokens['expires_in'], 
            'refresh_token': tokens['refresh_token'],
            'id': access_info['oid'],
            'username': access_info['unique_name']
            }

    oh_member = oh_code_to_member(data)

    if oh_member:
        # Log in the user.
        user = oh_member.user
        login(request, user,
              backend='django.contrib.auth.backends.ModelBackend')
        return redirect("/dashboard")

    logger.debug('Invalid code exchange. User returned to starting page.')
    return redirect('/')


@login_required(login_url="/")
def logout_user(request):
    """
    Logout user
    """
    if request.method == 'POST':
        logout(request)
    return redirect('index')


@login_required(login_url='/')
def dashboard(request):
    oh_member = request.user.oh_member
    context = {
        'oh_member': oh_member,
    }
    try:
        # oh_member_data = api.exchange_oauth2_member(
        #                     oh_member.get_access_token())
        # TBD: for now we'll have a simple mock data structure
        oh_member_data = {
            'data': [{
                'source': 'direct-sharing-71',
                'basename': 'pyspark_local_example.ipynb',
                'url' : 'file:///code/pyspark_local_example.ipynb'

            },
            {
                'source': 'direct-sharing-71',
                'basename': 'iris_example.ipynb',
                'url' : 'file:///code/iris_example.ipynb'

            },
                        {
                'source': 'direct-sharing-71',
                'basename': 'jupyterhub-setup.pdf',
                'url' : 'file:///code/jupyterhub-setup.pdf'

            },
                        {
                'source': 'direct-sharing-71',
                'basename': 'python_example.py',
                'url' : 'file:///code/python_example.py'

            }]
        }
    except:
        messages.error(request, "You need to re-authenticate with Open Humans")
        logout(request)
        return redirect("/")
    all_available_notebooks = get_notebook_files(oh_member_data)
    existing_notebooks = SharedNotebook.objects.filter(oh_member=oh_member)
    context = {
        'notebook_files': all_available_notebooks,
        'existing_notebooks': existing_notebooks,
        'JH_URL': settings.JUPYTERHUB_BASE_URL,
        'base_url': request.build_absolute_uri("/").rstrip('/'),
        'section': 'dashboard'}
    return render(request, 'main/dashboard.html',
                  context=context)


@login_required(login_url='/')
def likes(request):
    oh_member = request.user.oh_member
    liked_notebook_list = oh_member.notebooklike_set.all().order_by('-created_at')
    liked_notebooks = paginate_items(
                        liked_notebook_list,
                        request.GET.get('page'))
    return render(request, 'main/likes.html',
                  context={'liked_notebooks': liked_notebooks,
                           'section': 'likes'})


@login_required(login_url='/')
def add_notebook(request, notebook_url, notebook_name):
    oh_member = request.user.oh_member
    # TBD: Remove it
    # try:
    #     oh_member_data = api.exchange_oauth2_member(
    #                             oh_member.get_access_token())
    # except:
    #     print('.... EXCEPTION....')
    #     messages.error(request, "You need to re-authenticate with Open Humans")
    #     logout(request)
    #     return redirect("/")

    # notebook_name, notebook_url = get_notebook_oh(oh_member_data, notebook_id)

    if request.method == 'POST':
        add_notebook_helper(request, notebook_url, notebook_name, oh_member)
        return redirect('/dashboard')
    else:
        if len(SharedNotebook.objects.filter(oh_member=oh_member,
                                             notebook_name=notebook_name)) > 0:
            existing_notebook = SharedNotebook.objects.get(
                                        oh_member=oh_member,
                                        notebook_name=notebook_name)
            context = {'description': existing_notebook.description,
                       'tags': existing_notebook.get_tags(),
                       'data_sources': existing_notebook.get_data_sources(),
                       'notebook_name': notebook_name,
                       'notebook_url': str(notebook_url),
                       'edit': True}
        else:
            notebook_content = download_notebook_oh(notebook_url)
            suggested_sources = suggest_data_sources(notebook_content)
            context = {'description': '',
                       'notebook_name': notebook_name,
                       'notebook_url': str(notebook_url),
                       'tags': '',
                       'data_sources': suggested_sources}
        return render(request, 'main/add_notebook.html', context=context)


@login_required(login_url="/")
def edit_notebook(request, notebook_id):
    oh_member = request.user.oh_member
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    if notebook.oh_member != oh_member:
        messages.warning(request, 'Permission denied!')
        return redirect("/")
    if request.method == "POST":
        notebook.description = request.POST.get('description')
        tags = request.POST.get('tags')
        tags = [tag.strip() for tag in tags.split(',')]
        notebook.tags = json.dumps(tags)
        data_sources = request.POST.get('data_sources')
        data_sources = [ds.strip() for ds in data_sources.split(',')]
        notebook.data_sources = json.dumps(data_sources)
        notebook.updated_at = arrow.now().format()
        notebook.save()
        messages.info(request, 'Updated {}!'.format(notebook.notebook_name))
        return redirect("/dashboard")
    else:
        context = {'description': notebook.description,
                   'tags': notebook.get_tags(),
                   'data_sources': notebook.get_data_sources(),
                   'name': notebook.notebook_name,
                   'notebook_id': str(notebook_id)}
        return render(request, 'main/edit_notebook.html', context=context)


@login_required(login_url="/")
def delete_notebook(request, notebook_id):
    if request.method == "POST":
        oh_member = request.user.oh_member
        notebook = SharedNotebook.objects.get(pk=notebook_id)
        if notebook.oh_member != oh_member:
            messages.warning(request, 'Permission denied!')
            return redirect("/")
        notebook.delete()
        messages.info(request, 'Deleted {}!'.format(notebook.notebook_name))
        return redirect("/dashboard")


def notebook_index(request):
    order_variable = request.GET.get('order_by', 'updated_at')
    data_sources = get_all_data_sources()
    data_sources = sorted(data_sources)
    if order_variable not in ['updated_at', 'likes', 'views']:
        order_variable = 'updated_at'
    source_filter = request.GET.get('source', None)
    if source_filter:
        notebook_list = find_notebook_by_keywords(
                            source_filter,
                            search_field='data_sources')
    else:
        notebook_list = SharedNotebook.objects.filter(
            master_notebook=None)
    if order_variable == 'likes':
        notebook_list = notebook_list.annotate(
            likes=Count('notebooklike'))
    notebook_list = notebook_list.order_by('-{}'.format(order_variable))
    notebooks = paginate_items(notebook_list, request.GET.get('page'))
    return render(request,
                  'main/notebook_index.html',
                  {'notebooks': notebooks,
                   'section': 'explore',
                   'order_by': order_variable,
                   'data_sources': data_sources,
                   'source': source_filter})


def search_notebooks(request):
    if request.method == "POST":
        search_term = request.POST.get('search_term')
        notebook_list = find_notebook_by_keywords(search_term)
    else:
        search_term = request.GET.get('search_term', '')
        search_field = request.GET.get('search_field', None)
        notebook_list = find_notebook_by_keywords(search_term, search_field)
    order_variable = request.GET.get('order_by', 'updated_at')
    if order_variable not in ['updated_at', 'likes', 'views']:
        order_variable = 'updated_at'
    if order_variable == 'likes':
        notebook_list = notebook_list.annotate(
            likes=Count('notebooklike'))
    notebook_list = notebook_list.order_by('-{}'.format(order_variable))
    notebooks = paginate_items(notebook_list, request.GET.get('page'))
    return render(request,
                  'main/search.html',
                  {'notebooks': notebooks,
                   'order_by': order_variable,
                   'search_term': search_term})


def notebook_by_source(request):
    source_name = request.GET.get('source')
    notebook_list = []
    notebooks = SharedNotebook.objects.filter(
                        data_sources__contains=source_name,
                        master_notebook=None)
    notebooks = notebooks.annotate(
        likes=Count('notebooklike'))
    for notebook in notebooks:
        notebook_list.append(
            {
                'name': notebook.notebook_name,
                'user': notebook.oh_member.oh_username,
                'description': notebook.description,
                'views': notebook.views,
                'likes': notebook.likes,
                'details_url': request.build_absolute_uri(
                    reverse('notebook-details', args=[notebook.id])),
                'preview_url': request.build_absolute_uri(
                    reverse('render-notebook', args=[notebook.id])),
                'open_url': request.build_absolute_uri(
                    reverse('open-notebook', args=[notebook.id])
                )
            }
        )
    notebook_list = sorted(
        notebook_list,
        key=lambda k: k['views'], reverse=True)
    output = {
        'source_name': source_name, 'hits': len(notebook_list),
        'notebooks': notebook_list}
    return JsonResponse(output)


@csrf_exempt
def nbupload(request):
    if request.method != 'POST':
        return HttpResponse('Unexpected method.', status=405)

    access_token = request.headers.get('Authorization')
    print('in nbupload() -> access_token:' + access_token)
    if not access_token:
        return HttpResponse(status=401)
    if access_token.startswith(AUTHORIZATION_TYPE):
        access_token = access_token[len(AUTHORIZATION_TYPE):]

    decoded = verify_and_decode(access_token)
    if not decoded:
        return HttpResponse(status=401)
    decoded = jwt.decode(access_token, verify=False)
    print('>>> in nbupload() -> access_info:', decoded)

    data = {
            'id': decoded.get('oid'),
            'username': decoded.get('unique_name'),
            'access_token': access_token,
            'expires_in': decoded.get('exp'),
            'refresh_token': ''  # TODO
            }
    oh_member = oh_code_to_member(data)

    notebook_name = request.POST.get('notebook_name')
    notebook_content = request.POST.get('notebook_contents')
    add_notebook_direct(request, oh_member, notebook_name, notebook_content)
    
    return HttpResponse(status=200)
