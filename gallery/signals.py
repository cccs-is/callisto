from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import SharedDocument


@receiver(post_delete, sender=SharedDocument)
def my_handler(sender, instance, **kwargs):
    documents = SharedDocument.objects.filter(
                document_name=instance.document_name, published=True).order_by('created_at')
    if documents:
        master_nb = documents[0]
        for document in documents[1:]:
            document.master_document = master_nb
            document.save()
