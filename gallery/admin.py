from django.contrib import admin

from .models import SharedDocument, DocumentComment, DocumentLike, HubSpace, HubUser

admin.site.register(HubSpace)
admin.site.register(HubUser)

admin.site.register(SharedDocument)
admin.site.register(DocumentComment)
admin.site.register(DocumentLike)

