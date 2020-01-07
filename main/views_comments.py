import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from .models import SharedNotebook, NotebookComment

import arrow
# Set up logging.
logger = logging.getLogger(__name__)


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
