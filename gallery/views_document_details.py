from django.contrib.auth.decorators import login_required
from gallery.doc_types.doc_type_manager import doc_type_manager
from gallery.models import SharedDocument, DocumentLike
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
import arrow
from django.contrib import messages


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

    body = doc_type_manager.render(request, document)
    open_as = doc_type_manager.export_label(document)
    context = {'document': document,
               'other_documents': other_documents,
               'document_preview': body,
               'open_label': open_as,
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


@login_required
def render_document(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)
    body = doc_type_manager.render(request, document)
    return HttpResponse(body)


@login_required
def open_document_hub(request, document_id):
    document = SharedDocument.objects.get(pk=document_id)
    nbview_session_key = 'nb-view-{}'.format(document_id)
    if not request.session.get(nbview_session_key):
        request.session[nbview_session_key] = True
        document.views += 1
        document.save()
    return doc_type_manager.exporter(request, document)
