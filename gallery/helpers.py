import arrow
from gallery.models import SharedNotebook
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from django.contrib import messages
from collections import defaultdict

logger = logging.getLogger(__name__)


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


def add_notebook_direct(request, hub_member, notebook_name, notebook_content):
    notebook, created = SharedNotebook.objects.get_or_create(hub_member=hub_member, notebook_name=notebook_name)
    notebook.notebook_content = notebook_content
    notebook.notebook_name = notebook_name
    notebook.updated_at = arrow.now().format()
    notebook.hub_member = hub_member
    notebook.master_notebook = identify_master_notebook(notebook_name, hub_member)
    notebook.tags = '{}'
    notebook.data_sources = '{}'
    if created:
        notebook.created_at = arrow.now().format()
        messages.info(request, 'Your notebook {} has been uploaded!'.format(notebook_name))
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
