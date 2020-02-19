import logging
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from .helpers import find_document_by_keywords, get_all_data_sources
from .helpers import paginate_items
from .helpers import get_all_data_sources_numeric
from .models import SharedDocument, DocumentComment, HubSpace, SpaceTypes
import arrow
import json
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, get_user_model
from gallery.doc_types.doc_type_manager import doc_type_manager


# Set up logging.
logger = logging.getLogger(__name__)


@login_required
def shared(request):
        messages.info(request,
                      ("Your document was uploaded into your Open Humans account and can now be shared from here!"))
        return redirect('/dashboard')


# TODO why '/documents' ?
@login_required
def index(request):
    return redirect('/documents')


def data_source_index(request):
    data_sources = get_all_data_sources_numeric()
    return render(request, 'gallery/sources_index.html', {
                'section': 'sources',
                'data_sources': data_sources})


def about(request):
    return render(request, 'gallery/about.html', {'section': 'about'})


@login_required
def delete_user(request):
    if request.method == "POST":
        request.user.delete()
        messages.info(request, "Your account was deleted!")
        logout(request)
    return redirect('index')


def login_user(request):
    user = authenticate(request)
    if user is not None:
        login(request, user)
        next_url = request.GET.get('next')
        if not next_url:
            next_url = '/dashboard'
        return redirect(next_url)
    else:
        return redirect('/admin/login')


@login_required
def logout_user(request):
    """
    Logout user
    """
    if request.method == 'POST':
        logout(request)
    return redirect('about')


@login_required
def dashboard(request):
    hub_member = request.user
    existing_documents = SharedDocument.objects.filter(hub_member=hub_member, published=True)
    documents_to_publish = SharedDocument.objects.filter(hub_member=hub_member, published=False)
    context = {
        'existing_documents': existing_documents,
        'documents_to_publish': documents_to_publish,
        'section': 'dashboard'}
    return render(request, 'gallery/dashboard.html', context=context)


@login_required
def likes(request):
    hub_member = request.user
    liked_document_list = hub_member.documentlike_set.all().order_by('-created_at')
    liked_document_list = [x for x in liked_document_list if x.document.can_read(request.user)]
    liked_documents = paginate_items(liked_document_list, request.GET.get('page'))
    context = {'liked_documents': liked_documents, 'section': 'likes'}
    return render(request, 'gallery/likes.html', context=context)


@login_required
def edit_document(request, document_id):
    hub_member = request.user
    document = SharedDocument.objects.get(pk=document_id)
    if document.hub_member != hub_member:
        messages.warning(request, 'Permission denied!')
        return redirect("/")
    if request.method == "POST":
        document.description = request.POST.get('description')
        spaces_id = request.POST.getlist('spaces')
        document_name = request.POST.get('document_name')
        if document_name:
            document.document_name = document_name
        document_type = request.POST.get('document_type')
        if document_type:
            document.document_type = document_type
        document.spaces.clear()
        for space_id in spaces_id:
            space = HubSpace.objects.get(pk=space_id)
            document.spaces.add(space)
        tags = request.POST.get('tags')
        tags = [tag.strip() for tag in tags.split(',')]
        document.tags = json.dumps(tags)
        data_sources = request.POST.get('data_sources')
        data_sources = [ds.strip() for ds in data_sources.split(',')]
        document.data_sources = json.dumps(data_sources)
        document.updated_at = arrow.now().format()
        document.published = True
        document.save()
        messages.info(request, 'Updated {}!'.format(document.document_name))
        return redirect("/dashboard")
    else:
        available_spaces = {x for x in HubSpace.objects.all() if x.can_write(hub_member)}
        selected_spaces = document.spaces.all()
        available_doc_types = doc_type_manager.available_doc_types()
        context = {'document': document,
                   'description': document.description,
                   'available_doc_types': available_doc_types,
                   'spaces': available_spaces,
                   'selected_spaces': selected_spaces,
                   'tags': document.get_tags(),
                   'data_sources': document.get_data_sources(),
                   'document_name': document.document_name,
                   'document_id': str(document_id),
                   'edit': document.published}
        return render(request, 'gallery/edit_document.html', context=context)


@login_required
def delete_document(request, document_id):
    if request.method == "POST":
        hub_member = request.user
        document = SharedDocument.objects.get(pk=document_id)
        if document.hub_member != hub_member:
            messages.warning(request, 'Permission denied!')
            return redirect("/")
        document.delete()
        messages.info(request, 'Deleted {}!'.format(document.document_name))
        return redirect("/dashboard")


def document_index(request):
    order_variable = request.GET.get('order_by', 'updated_at')
    data_sources = get_all_data_sources()
    data_sources = sorted(data_sources)
    if order_variable not in ['updated_at', 'likes', 'views']:
        order_variable = 'updated_at'

    source_filter = request.GET.get('source', None)
    type_filter = request.GET.get('type', None)
    space_filter = request.GET.get('space', None)
    if space_filter:
        try:
            space_filter = int(space_filter)
        except ValueError:
            space_filter = None

    document_list = SharedDocument.objects.filter(master_document=None, published=True)
    # collect all visible spaces
    document_spaces = set()
    for document in document_list:
        for space in document.spaces.all():
            if space not in document_spaces:
                if space.can_read(request.user):
                    document_spaces.add(space)
    if space_filter:
        document_list = document_list.filter(spaces__pk=space_filter)
    if source_filter:
        document_list = document_list.filter(data_sources__contains=source_filter)
    if type_filter:
        document_list = document_list.filter(document_type=type_filter)

    if order_variable == 'likes':
        document_list = document_list.annotate(
            likes=Count('documentlike'))
    document_list = document_list.order_by('-{}'.format(order_variable))
    document_list = [x for x in document_list if x.can_read(request.user)]
    documents = paginate_items(document_list, request.GET.get('page'))
    return render(request,
                  'gallery/document_index.html',
                  {'documents': documents,
                   'section': 'explore',
                   'order_by': order_variable,
                   'data_sources': data_sources,
                   'document_spaces': document_spaces,
                   'available_document_types': doc_type_manager.available_doc_types(),
                   'selected_document_type': type_filter,
                   'source': source_filter,
                   'space': space_filter
                   })


@login_required
def search_documents(request):
    if request.method == "POST":
        search_term = request.POST.get('search_term')
        document_list = find_document_by_keywords(search_term)
    else:
        search_term = request.GET.get('search_term', '')
        search_field = request.GET.get('search_field', None)
        document_list = find_document_by_keywords(search_term, search_field)
    order_variable = request.GET.get('order_by', 'updated_at')
    if order_variable not in ['updated_at', 'likes', 'views']:
        order_variable = 'updated_at'
    if order_variable == 'likes':
        document_list = document_list.annotate(
            likes=Count('documentlike'))
    document_list = document_list.order_by('-{}'.format(order_variable))
    document_list = [x for x in document_list if x.can_read(request.user)]
    documents = paginate_items(document_list, request.GET.get('page'))
    return render(request,
                  'gallery/search.html',
                  {'documents': documents,
                   'order_by': order_variable,
                   'search_term': search_term})


def document_by_source(request):
    source_name = request.GET.get('source')
    document_list = []
    documents = SharedDocument.objects.filter(
        data_sources__contains=source_name,
        master_document=None,
        published=True)
    documents = documents.annotate(
        likes=Count('documentlike'))
    for document in documents:
        document_list.append(
            {
                'name': document.document_name,
                'user': '{0} {1}'.format(document.hub_member.first_name,document.hub_member.last_name),
                'description': document.description,
                'views': document.views,
                'likes': document.likes,
                'details_url': request.build_absolute_uri(
                    reverse('document-details', args=[document.id])),
                'preview_url': request.build_absolute_uri(
                    reverse('render-document', args=[document.id])),
                'open_url': request.build_absolute_uri(
                    reverse('open-document', args=[document.id])
                )
            }
        )
    document_list = sorted(
        document_list,
        key=lambda k: k['views'], reverse=True)
    output = {
        'source_name': source_name, 'hits': len(document_list),
        'documents': document_list}
    return JsonResponse(output)


@login_required
def add_comment(request, document_id):
    if request.method == "POST":
        hub_member = request.user
        document = SharedDocument.objects.get(pk=document_id)
        comment = DocumentComment(
            hub_member=hub_member,
            document=document,
            created_at=arrow.now().format(),
            comment_text=request.POST.get('comment_text')
        )
        comment.save()
        messages.info(request, "Your comment has been posted")
        return redirect(reverse('document-details', args=(document_id,)))


@login_required
def upload_document(request):
    hub_member = request.user
    if request.method == 'POST' and request.FILES.getlist('upload_files'):
        files = request.FILES.getlist('upload_files')
        for f in files:
            document_content = ''
            for chunk in f.chunks():
                document_content += chunk.decode("utf-8")
            document_name = f.name

            document_type = doc_type_manager.doc_type(document_name, document_content)
            # TODO default doc type <- now might be None
            doc_type_manager.importer(request, document_type, document_name, document_content)
        return redirect("/dashboard")
    return render(request, 'gallery/upload_document.html')


# TODO rename document_upload
@csrf_exempt
def nbupload(request):
    if request.method != 'POST':
       return HttpResponse('Unexpected method.', status=405)
    # We have to do this explicitly as @login_required will come back as GET request, not POST:
    user = request.user
    if not user.is_authenticated:
        user = authenticate(request)
        if user is None:
            return HttpResponse(status=401)
        login(request, user)

    document_name = request.POST.get('notebook_name')  # FIXME document_name
    document_content = request.POST.get('notebook_contents')  # FIXME document_contents

    # FIXME make the endpoint more generic, require doc type to be passed in
    doc_type_manager.importer(request, 'notebook', document_name, document_content)
    return HttpResponse(status=200)


@login_required
def spaces_index(request):
    hub_member = request.user
    if request.method == "POST":
        # Create a new space and open its detail page
        space_name = hub_member.get_full_name() + '-HubSpace-' + str(datetime.now(tz=None))
        space = HubSpace.objects.create(space_name=space_name, type=SpaceTypes.Private.value)
        space.save()
        space.spaces_admin.add(hub_member)
        space.save()
        space_id = space.pk
        return redirect("/space/" + str(space_id))
    else:
        order_variable = request.GET.get('order_by', 'name')
        if order_variable not in ['name', 'access']:
            order_variable = 'name'
        spaces = [x for x in HubSpace.objects.all() if hub_member.is_superuser or x.can_read(hub_member)]

        if order_variable == 'access':
            spaces = sorted(spaces, key=lambda t: t.access(hub_member).value)
        else:
            spaces = sorted(spaces, key=lambda t: t.space_name)

        spaces = paginate_items(spaces, request.GET.get('page'))
        context = {
            'spaces': spaces,
            'order_by': order_variable,
            'section': 'spaces-index'
        }
        return render(request, 'gallery/spaces_index.html', context=context)


@login_required
def spaces_delete(request, space_id):
    hub_member = request.user
    space = HubSpace.objects.get(pk=space_id)
    all_space_types = SpaceTypes.choices()

    # only admin or space admin can edit the space
    if not hub_member.is_superuser:
        if hub_member not in space.spaces_admin.all():
            messages.warning(request, 'Permission denied!')
            return redirect("/space")

    if request.method == "POST":
        space.delete()
        return redirect("/space")
    else:
        messages.warning(request, 'Invalid operation')
        return redirect("/space")


@login_required
def spaces_details(request, space_id):
    hub_member = request.user
    space = HubSpace.objects.get(pk=space_id)
    all_space_types = SpaceTypes.choices()

    # only admin or space admin can edit the space
    if not hub_member.is_superuser:
        if hub_member not in space.spaces_admin.all():
            messages.warning(request, 'Permission denied!')
            return redirect("/space")

    if request.method == "POST":
        space.space_name = request.POST.get('hub_space_name')
        space.space_description = request.POST.get('description')
        space.type = request.POST.get('type')
        space.save()
        messages.info(request, 'Updated {}!'.format(space.space_name))
        return redirect("/space")
    else:
        user_model = get_user_model()
        all_users = user_model.objects.all()
        context = {'space_name': space.space_name,
                   'description': space.space_description,
                   'space_id': str(space_id),
                   'all_space_types': all_space_types,
                   'space': space,
                   'all_users': all_users,
                   'edit': True} # TODO
        return render(request, 'gallery/spaces_details.html', context=context)


@login_required
def spaces_users(request, space_id):
    hub_member = request.user
    space = HubSpace.objects.get(pk=space_id)

    # only admin or space admin can edit the space
    if not hub_member.is_superuser:
        if hub_member not in space.spaces_admin.all():
            messages.warning(request, 'Permission denied!')
            return redirect("/space")

    if request.method == "POST":
        change_users = request.POST.getlist('users')
        action = request.POST.get('action')
        user_model = get_user_model()
        for username in change_users:
            user = user_model.objects.get(username=username)
            if action == 'admin-add':
                space.spaces_admin.add(user)
            elif action == 'admin-remove':
                space.spaces_admin.remove(user)
            elif action == 'read-add':
                space.spaces_read.add(user)
            elif action == 'read-remove':
                space.spaces_read.remove(user)
            elif action == 'write-add':
                space.spaces_write.add(user)
            elif action == 'write-remove':
                space.spaces_write.remove(user)
            else:
                return HttpResponse('Unexpected action: ' + str(action), status=500)
            user.save()
        space.save()
        return redirect("/space/" + str(space_id))
    else:
        action = request.GET.get('action')
        user_model = get_user_model()
        if action == 'admin-add':
            add_action = True
            list_group = 'Admins'
            all_users = user_model.objects.all()
            list_users = all_users.difference(space.spaces_admin.all())
        elif action == 'admin-remove':
            add_action = False
            list_group = 'Admins'
            list_users = space.spaces_admin.all()
        elif action == 'read-add':
            add_action = True
            list_group = 'Users-Read'
            all_users = user_model.objects.all()
            list_users = all_users.difference(space.spaces_read.all())
        elif action == 'read-remove':
            add_action = False
            list_group = 'Users-Read'
            list_users = space.spaces_read.all()
        elif action == 'write-add':
            add_action = True
            list_group = 'Users-Write'
            all_users = user_model.objects.all()
            list_users = all_users.difference(space.spaces_write.all())
        elif action == 'write-remove':
            add_action = False
            list_group = 'Users-Write'
            list_users = space.spaces_write.all()
        else:
            return HttpResponse('Unexpected action: ' + str(action), status=500)

        context = {'space_id': str(space_id),
                   'space': space,
                   'action': action,
                   'add': add_action,
                   'users': list_users,
                   'group': list_group}
        return render(request, 'gallery/add_users.html', context=context)
