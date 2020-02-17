import arrow
from gallery.models import SharedDocument
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from django.contrib import messages
from collections import defaultdict

logger = logging.getLogger(__name__)


def find_document_by_keywords(search_term, search_field=None):
    documents_tag = SharedDocument.objects.filter(
        tags__icontains=search_term,
        master_document=None,
        published=True)
    if search_field == 'tags':
        return documents_tag.order_by('updated_at')
    documents_space = SharedDocument.objects.filter(
        spaces__space_name__icontains=search_term,
        master_document=None,
        published=True)
    if search_field == 'spaces':
        return documents_space.order_by('updated_at')
    documents_source = SharedDocument.objects.filter(
        data_sources__icontains=search_term,
        master_document=None,
        published=True)
    if search_field == 'data_sources':
        return documents_source.order_by('updated_at')
    # TODO verify
    documents_user = SharedDocument.objects.filter(
        hub_member__username__icontains=search_term,
        master_document=None,
        published=True)
    if search_field == 'username':
        return documents_user.order_by('updated_at')
    documents_description = SharedDocument.objects.filter(
        description__icontains=search_term,
        master_document=None,
        published=True)
    documents_name = SharedDocument.objects.filter(
        document_name__icontains=search_term,
        master_document=None,
        published=True)
    nbs = documents_tag | documents_space | documents_source | documents_description | documents_name | documents_user
    nbs = nbs.order_by('updated_at')
    return nbs


def identify_master_document(document_name, hub_member):
    other_documents = SharedDocument.objects.filter(
                        document_name=document_name, published=True).exclude(
                        hub_member=hub_member).order_by('created_at')
    if other_documents:
        return other_documents[0]
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


def get_all_data_sources_numeric():
    sdict = defaultdict(int)
    for nb in SharedDocument.objects.filter(master_document=None, published=True):
        for source in nb.get_data_sources_json():
            sdict[source] += 1
    sorted_sdict = sorted(sdict.items(), key=lambda x: x[1], reverse=True)
    return sorted_sdict


def get_all_data_sources():
    sorted_sdict = get_all_data_sources_numeric()
    sources = [i[0] for i in sorted_sdict]
    return sources
