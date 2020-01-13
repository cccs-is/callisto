from django.contrib import admin

from .models import SharedNotebook, NotebookComment, NotebookLike

admin.site.register(SharedNotebook)
admin.site.register(NotebookComment)
admin.site.register(NotebookLike)