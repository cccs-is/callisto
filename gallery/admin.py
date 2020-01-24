from django.contrib import admin

from .models import SharedNotebook, NotebookComment, NotebookLike, HubSpace, HubUser

admin.site.register(HubSpace)
admin.site.register(HubUser)

admin.site.register(SharedNotebook)
admin.site.register(NotebookComment)
admin.site.register(NotebookLike)

