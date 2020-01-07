from django.db import models
from datetime import timedelta
import arrow
import json
from django.contrib.auth.models import User


def get_full_name(user):
    """
    Common method to get descriptive user's name
    """
    if user is None:
        return ''
    return '{0} {1}'.format(user.first_name, user.last_name)


class SharedNotebook(models.Model):
    hub_member = models.ForeignKey(User, on_delete=models.CASCADE)
    notebook_name = models.TextField(default='')
    notebook_content = models.TextField(default='')
    description = models.TextField(default='')
    tags = models.TextField(default='')
    data_sources = models.TextField(default='')
    views = models.IntegerField(default=0)
    updated_at = models.DateTimeField(default=(arrow.now() - timedelta(days=7)).format())
    created_at = models.DateTimeField(default=(arrow.now() - timedelta(days=7)).format())
    master_notebook = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)

    def full_user_name(self):
        return get_full_name(self.hub_member)

    def get_tags(self):
        return ",".join(json.loads(self.tags)) if self.tags else ''

    def get_data_sources(self):
        if self.data_sources:
            return ",".join(json.loads(self.data_sources))
        else:
            return ''

    def get_tags_json(self):
        return json.loads(self.tags)

    def get_data_sources_json(self):
        return json.loads(self.data_sources)


class NotebookComment(models.Model):
    """
    comments about a given notebook
    """
    hub_member = models.ForeignKey(User, on_delete=models.CASCADE)
    notebook = models.ForeignKey(SharedNotebook, on_delete=models.CASCADE)
    comment_text = models.TextField(default='')
    created_at = models.DateTimeField(default=arrow.now().format())

    def full_user_name(self):
        return get_full_name(self.hub_member)

    class Meta:
            ordering = ["created_at"]


class NotebookLike(models.Model):
    """
    like a given notebook
    """
    hub_member = models.ForeignKey(User, on_delete=models.CASCADE)
    notebook = models.ForeignKey(SharedNotebook, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=arrow.now().format())

    def full_user_name(self):
        return get_full_name(self.hub_member)
