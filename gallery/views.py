import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from .helpers import find_notebook_by_keywords, get_all_data_sources
from .helpers import add_notebook_direct
from .helpers import paginate_items
from .helpers import get_all_data_sources_numeric
from .models import SharedNotebook, NotebookComment
import arrow
import json
from django.db.models import Count
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login

# Set up logging.
logger = logging.getLogger(__name__)


@login_required
def shared(request):
        messages.info(request,
                      ("Your notebook was uploaded into your Open Humans account and can now be shared from here!"))
        return redirect('/dashboard')


# TODO why '/notebooks' ?
@login_required
def index(request):
    return redirect('/notebooks')


# TODO turn non-authenticated part of this into after-logout page?
def indexOLD(request):
    # otherwise
    latest_notebooks = SharedNotebook.objects.filter(master_notebook=None, published=True).order_by('-views')[:5]
    data_sources = get_all_data_sources()[:6]
    context = {'latest_notebooks': latest_notebooks,
               'data_sources': data_sources}
    return render(request, 'gallery/index.html', context=context)


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
    return redirect('index')


@login_required
def dashboard(request):
    hub_member = request.user
    existing_notebooks = SharedNotebook.objects.filter(hub_member=hub_member, published=True)
    notebooks_to_publish = SharedNotebook.objects.filter(hub_member=hub_member, published=False)
    context = {
        'existing_notebooks': existing_notebooks,
        'notebooks_to_publish': notebooks_to_publish,
        'section': 'dashboard'}
    return render(request, 'gallery/dashboard.html', context=context)


@login_required
def likes(request):
    hub_member = request.user
    liked_notebook_list = hub_member.notebooklike_set.all().order_by('-created_at')
    liked_notebooks = paginate_items(liked_notebook_list, request.GET.get('page'))
    context = {'liked_notebooks': liked_notebooks, 'section': 'likes'}
    return render(request, 'gallery/likes.html', context=context)


@login_required
def edit_notebook(request, notebook_id):
    hub_member = request.user
    notebook = SharedNotebook.objects.get(pk=notebook_id)
    if notebook.hub_member != hub_member:
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
        notebook.published = True
        notebook.save()
        messages.info(request, 'Updated {}!'.format(notebook.notebook_name))
        return redirect("/dashboard")
    else:
        context = {'description': notebook.description,
                   'tags': notebook.get_tags(),
                   'data_sources': notebook.get_data_sources(),
                   'notebook_name': notebook.notebook_name,
                   'notebook_id': str(notebook_id),
                   'edit': notebook.published}
        return render(request, 'gallery/edit_notebook.html', context=context)


@login_required
def delete_notebook(request, notebook_id):
    if request.method == "POST":
        hub_member = request.user
        notebook = SharedNotebook.objects.get(pk=notebook_id)
        if notebook.hub_member != hub_member:
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
        notebook_list = SharedNotebook.objects.filter(master_notebook=None, published=True)
    if order_variable == 'likes':
        notebook_list = notebook_list.annotate(
            likes=Count('notebooklike'))
    notebook_list = notebook_list.order_by('-{}'.format(order_variable))
    notebooks = paginate_items(notebook_list, request.GET.get('page'))
    return render(request,
                  'gallery/notebook_index.html',
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
                  'gallery/search.html',
                  {'notebooks': notebooks,
                   'order_by': order_variable,
                   'search_term': search_term})


def notebook_by_source(request):
    source_name = request.GET.get('source')
    notebook_list = []
    notebooks = SharedNotebook.objects.filter(
        data_sources__contains=source_name,
        master_notebook=None,
        published=True)
    notebooks = notebooks.annotate(
        likes=Count('notebooklike'))
    for notebook in notebooks:
        notebook_list.append(
            {
                'name': notebook.notebook_name,
                'user': '{0} {1}'.format(notebook.hub_member.first_name,notebook.hub_member.last_name),
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


@login_required
def add_comment(request, notebook_id):
    if request.method == "POST":
        hub_member = request.user
        notebook = SharedNotebook.objects.get(pk=notebook_id)
        comment = NotebookComment(
            hub_member=hub_member,
            notebook=notebook,
            created_at=arrow.now().format(),
            comment_text=request.POST.get('comment_text')
        )
        comment.save()
        messages.info(request, "Your comment has been posted")
        return redirect(reverse('notebook-details', args=(notebook_id,)))


@login_required
def upload_notebook(request):
    hub_member = request.user
    if request.method == 'POST' and request.FILES.getlist('upload_files'):
        files = request.FILES.getlist('upload_files')
        notebook_name = ''
        for f in files:
            notebook_content = ''
            for chunk in f.chunks():
                notebook_content += chunk.decode("utf-8")
            notebook_name = f.name
            add_notebook_direct(request, hub_member, notebook_name, notebook_content)
        return render(request, 'gallery/upload_notebook.html', {
            'uploaded_notebook': notebook_name
        })
    return render(request, 'gallery/upload_notebook.html')


# TODO rename notebook_upload
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

    notebook_name = request.POST.get('notebook_name')
    notebook_content = request.POST.get('notebook_contents')
    add_notebook_direct(request, user, notebook_name, notebook_content)

    return HttpResponse(status=200)
