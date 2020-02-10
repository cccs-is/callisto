from django.db import models
from datetime import timedelta
import arrow
import json
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from enum import Enum


class HubUser(AbstractUser):
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        If no last name and first name specified, return e-mail.
        """
        if self.first_name and self.last_name:
            full_name = '%s %s' % (self.first_name, self.last_name)
        else:
            full_name = self.email
        return full_name.strip()


class SpaceTypes(Enum):
    Private = 0
    AllCanRead = 1
    AllCanWrite = 2

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class AccessTypes(Enum):
    Admin = 0
    Read = 1
    Write = 2


class HubSpace(models.Model):
    space_name = models.TextField(default='')
    space_description = models.TextField(default='')
    type = models.IntegerField(choices=SpaceTypes.choices(), default=SpaceTypes.Private)
    spaces_read = models.ManyToManyField(HubUser, related_name='spaces_read', blank=True)
    spaces_write = models.ManyToManyField(HubUser, related_name='spaces_write', blank=True)
    spaces_admin = models.ManyToManyField(HubUser, related_name='spaces_admin', blank=True)

    def get_type_label(self):
        return SpaceTypes(self.type).name

    def can_admin(self, hub_member):
        return hub_member in self.spaces_admin.all()

    def can_write(self, hub_member):
        if self.can_admin(hub_member):
            return True
        if self.type == SpaceTypes.AllCanWrite.value:
            return True
        return hub_member in self.spaces_write.all()

    def can_read(self, hub_member):
        if self.can_write(hub_member):
            return True
        if self.type == SpaceTypes.AllCanRead.value:
            return True
        return hub_member in self.spaces_read.all()

    def access(self, hub_member):
        if self.can_admin(hub_member):
            return AccessTypes.Admin
        elif self.can_write(hub_member):
            return AccessTypes.Write
        elif self.can_read(hub_member):
            return AccessTypes.Read
        return None


class SharedNotebook(models.Model):
    hub_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notebook_name = models.TextField(default='')
    notebook_content = models.TextField(default='')
    description = models.TextField(default='')
    tags = models.TextField(default='')
    data_sources = models.TextField(default='')
    views = models.IntegerField(default=0)
    updated_at = models.DateTimeField(default=(arrow.now() - timedelta(days=7)).format())
    created_at = models.DateTimeField(default=(arrow.now() - timedelta(days=7)).format())
    master_notebook = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)
    published = models.BooleanField(default=False)
    spaces = models.ManyToManyField(HubSpace, related_name='spaces', blank=True)

    def full_user_name(self):
        return self.hub_member.get_full_name()

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

    def can_read(self, hub_member):
        if hub_member == self.hub_member:
            return True
        spaces_can_read = {x for x in HubSpace.objects.all() if x.can_read(hub_member)}
        return spaces_can_read & set(self.spaces.all())


class NotebookComment(models.Model):
    """
    comments about a given notebook
    """
    hub_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notebook = models.ForeignKey(SharedNotebook, on_delete=models.CASCADE)
    comment_text = models.TextField(default='')
    created_at = models.DateTimeField(default=arrow.now().format())

    def full_user_name(self):
        return self.hub_member.get_full_name()

    class Meta:
            ordering = ["created_at"]


class NotebookLike(models.Model):
    """
    like a given notebook
    """
    hub_member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notebook = models.ForeignKey(SharedNotebook, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=arrow.now().format())
