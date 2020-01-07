import requests
import arrow
import json
import requests_oauthlib

from django.conf import settings
from django.urls import reverse
from main.models import SharedNotebook
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ohapi import api
from urllib.parse import urlparse
import logging
from open_humans.models import OpenHumansMember
from django.contrib import messages
from collections import defaultdict

logger = logging.getLogger(__name__)


def get_notebook_files(oh_member_data):
    files = [i for i in oh_member_data['data']
             if i['source'] == 'direct-sharing-71']
    return files


def get_notebook_oh(oh_member_data, notebook_id):
    for data_object in oh_member_data['data']:
        if str(data_object['id']) == notebook_id:
            return (data_object['basename'], data_object['download_url'])


# Temp local reader for testing.... for now.
def local_get(url):
    p_url = urlparse(url)
    if p_url.scheme != 'file':
        raise ValueError("Expected file scheme")

    filename = p_url.path
    content = ''
    with open(filename, 'r') as f:
        content = f.read()
    return content


def download_notebook_oh(notebook_url):
    if notebook_url.startswith('file:///'):
        return local_get(notebook_url)

    notebook_content = requests.get(notebook_url).content
    return notebook_content

# TODO Remove
def create_notebook_link(notebook, request):
    base_url = request.build_absolute_uri("/").rstrip('/')
    print('>> create_notebook_link() -> base_url:', base_url)
    target = request.GET.get('target', '')
    if target == 'voila':
        target = "&target=voila"
    else:
        target = ''
    if request.user.is_authenticated:
        oh_member=request.user.username
        access_token = oh_member.access_token
    jupyterhub_url = settings.JUPYTERHUB_BASE_URL
    export_url = reverse('export-notebook', args=(notebook.id,))
    notebook_link = '{}/notebook-import?notebook_location={}{}&notebook_name={}&access_token={}{}'.format(
        jupyterhub_url,
        base_url,
        export_url,
        notebook.notebook_name,
        access_token,
        target
    )
    return notebook_link


def find_notebook_by_keywords(search_term, search_field=None):
    notebooks_tag = SharedNotebook.objects.filter(
        tags__contains=search_term,
        master_notebook=None)
    if search_field == 'tags':
        return notebooks_tag.order_by('updated_at')
    notebooks_source = SharedNotebook.objects.filter(
                        data_sources__contains=search_term,
                        master_notebook=None)
    if search_field == 'data_sources':
        return notebooks_source.order_by('updated_at')
    # TODO verify
    notebooks_user = SharedNotebook.objects.filter(
                        hub_member__username__contains=search_term,
                        master_notebook=None)
    if search_field == 'username':
        return notebooks_user.order_by('updated_at')
    notebooks_description = SharedNotebook.objects.filter(
                        description__contains=search_term,
                        master_notebook=None)
    notebooks_name = SharedNotebook.objects.filter(
                        notebook_name__contains=search_term,
                        master_notebook=None)

    nbs = notebooks_tag | notebooks_source | notebooks_description | notebooks_name | notebooks_user
    nbs = nbs.order_by('updated_at')
    return nbs


def suggest_data_sources(notebook_content):
    potential_sources = re.findall("direct-sharing-\d+", str(notebook_content))
    print('TBD: suggest_data_sources() Implement ME!')
    return ""
    
    if potential_sources:
        response = requests.get(
            'https://www.openhumans.org/api/public-data/members-by-source/')
        results = response.json()['results']
        while response.json()['next']:
            response = requests.get(
              'https://www.openhumans.org/api/public-data/members-by-source/')
            results.append(response.json()['results'])
        source_names = {i['source']: i['name'] for i in results}
        suggested_sources = [source_names[i] for i in potential_sources
                             if i in source_names]
        suggested_sources = list(set(suggested_sources))
        return ",".join(suggested_sources)
    return ""


def identify_master_notebook(notebook_name, hub_member):
    other_notebooks = SharedNotebook.objects.filter(
                        notebook_name=notebook_name).exclude(
                        hub_member=hub_member).order_by('created_at')
    if other_notebooks:
        return other_notebooks[0]
    return None


def paginate_items(queryset, page):
    paginator = Paginator(queryset, 10)
    try:
        paged_queryset = paginator.page(page)
    except PageNotAnInteger:
        paged_queryset = paginator.page(1)
    except EmptyPage:
        paged_queryset = paginator.page(paginator.num_pages)
    return paged_queryset


def oh_code_to_member(data):
    """
    Exchange data for token, use this to create and return OrgMember.
    If a matching OrgMember exists, update and return it.
    """
    if data:

        # TBD, we need to have thsi OAuth2Session held by the model someow
        # TBD, we need to have the state is set here and checked against the
        #      returned state.
                           

        # data = {
        #     'grant_type': 'authorization_code',
        #     'redirect_uri':
        #     '{}/complete'.format(settings.OPENHUMANS_APP_BASE_URL),
        #     'code': code,
        # }
        # req = requests.post(
        #     '{}/oauth2/token/'.format(settings.OPENHUMANS_OH_BASE_URL),
        #     data=data,
        #     auth=requests.auth.HTTPBasicAuth(
        #         settings.OPENHUMANS_CLIENT_ID,
        #         settings.OPENHUMANS_CLIENT_SECRET
        #     )
        # )
        # data = req.json()

        if 'access_token' in data:
            oh_id = data['id']
            oh_username = data['username']
            try:
                oh_member = OpenHumansMember.objects.get(oh_id=oh_id)
                logger.debug('Member {} re-authorized.'.format(oh_id))
                access_token = data.get('access_token')
                if access_token:
                    oh_member.access_token = access_token
                refresh_token = data.get('refresh_token')
                if refresh_token:
                    oh_member.refresh_token = refresh_token
                expires_in = data.get('expires_in')
                if expires_in:
                    oh_member.token_expires = OpenHumansMember.get_expiration(expires_in)
            except OpenHumansMember.DoesNotExist:
                oh_member = OpenHumansMember.create(
                    oh_id=oh_id,
                    oh_username=oh_username,
                    access_token=data.get('access_token'),
                    refresh_token=data.get('refresh_token'),
                    expires_in=data.get('expires_in'))  # TODO this does not match update case which goes via OpenHumansMember.get_expiration(expires_in)
                logger.debug('Member {} created.'.format(oh_id))
            oh_member.save()

            return oh_member

        # elif 'error' in req.json():
        #     logger.debug('Error in token exchange: {}'.format(req.json()))
        else:
            logger.warning('Neither token nor error info in OH response!')
    else:
        logger.error('OH_CLIENT_SECRET or code are unavailable')
    return None


def add_notebook_helper(request, notebook_url, notebook_name, hub_member):
    notebook_content = download_notebook_oh(notebook_url)
    notebook, created = SharedNotebook.objects.get_or_create(
                                            hub_member=hub_member,
                                            notebook_name=notebook_name)
    notebook.description = request.POST.get('description')
    tags = request.POST.get('tags')
    tags = [tag.strip() for tag in tags.split(',')]
    notebook.tags = json.dumps(tags)
    data_sources = request.POST.get('data_sources')
    data_sources = [ds.strip() for ds in data_sources.split(',')]
    notebook.data_sources = json.dumps(data_sources)
    notebook.notebook_name = notebook_name
    notebook.notebook_content = notebook_content # notebook_content.decode()
    notebook.updated_at = arrow.now().format()
    notebook.hub_member = hub_member
    notebook.master_notebook = identify_master_notebook(notebook_name,
                                                        hub_member)
    if created:
        notebook.created_at = arrow.now().format()
        messages.info(request, 'Your notebook {} has been shared!'.format(
            notebook_name
        ))
    else:
        messages.info(request, 'Your notebook {} has been updated!'.format(
            notebook_name
        ))
    notebook.save()


def add_notebook_direct(request, hub_member, notebook_name, notebook_content):
    notebook, created = SharedNotebook.objects.get_or_create(hub_member=hub_member, notebook_name=notebook_name)
    notebook.notebook_content = notebook_content  # TODO: .decode() - do we need to encode / decode if passed as data?
    notebook.notebook_name = notebook_name
    notebook.updated_at = arrow.now().format()
    notebook.hub_member = hub_member
    notebook.master_notebook = identify_master_notebook(notebook_name, hub_member)
    notebook.tags = '{}'
    notebook.data_sources = '{}'
    if created:
        notebook.created_at = arrow.now().format()
        messages.info(request, 'Your notebook {} has been shared!'.format(notebook_name))
    else:
        messages.info(request, 'Your notebook {} has been updated!'.format(notebook_name))
    notebook.save()


def get_all_data_sources_numeric():
    sdict = defaultdict(int)
    for nb in SharedNotebook.objects.filter(master_notebook=None):
        for source in nb.get_data_sources_json():
            sdict[source] += 1
    sorted_sdict = sorted(sdict.items(), key=lambda x: x[1], reverse=True)
    return sorted_sdict


def get_all_data_sources():
    sorted_sdict = get_all_data_sources_numeric()
    sources = [i[0] for i in sorted_sdict]
    return sources
