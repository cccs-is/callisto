import requests
import arrow
import json
from gallery.models import SharedNotebook
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlparse
import logging
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


def find_notebook_by_keywords(search_term, search_field=None):
    notebooks_tag = SharedNotebook.objects.filter(
        tags__contains=search_term,
        master_notebook=None,
        published=True)
    if search_field == 'tags':
        return notebooks_tag.order_by('updated_at')
    notebooks_source = SharedNotebook.objects.filter(
        data_sources__contains=search_term,
        master_notebook=None,
        published=True)
    if search_field == 'data_sources':
        return notebooks_source.order_by('updated_at')
    # TODO verify
    notebooks_user = SharedNotebook.objects.filter(
        hub_member__username__contains=search_term,
        master_notebook=None,
        published=True)
    if search_field == 'username':
        return notebooks_user.order_by('updated_at')
    notebooks_description = SharedNotebook.objects.filter(
        description__contains=search_term,
        master_notebook=None,
        published=True)
    notebooks_name = SharedNotebook.objects.filter(
        notebook_name__contains=search_term,
        master_notebook=None,
        published=True)
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
                        notebook_name=notebook_name, published=True).exclude(
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

# TODO this is used for original population from files. Remove after we add file upload.
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
    notebook.published = True
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
    for nb in SharedNotebook.objects.filter(master_notebook=None, published=True):
        for source in nb.get_data_sources_json():
            sdict[source] += 1
    sorted_sdict = sorted(sdict.items(), key=lambda x: x[1], reverse=True)
    return sorted_sdict


def get_all_data_sources():
    sorted_sdict = get_all_data_sources_numeric()
    sources = [i[0] for i in sorted_sdict]
    return sources
