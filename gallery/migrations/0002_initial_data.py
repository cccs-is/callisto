import os
from django.db import migrations
from django.contrib.auth import get_user_model


def generate_superuser(apps, schema_editor):
    callisto_admin_name = os.environ.get('CALLISTO_ADMIN_NAME')
    callisto_admin_email = os.environ.get('CALLISTO_ADMIN_EMAIL')
    callisto_admin_password = os.environ.get('CALLISTO_ADMIN_PASSWORD')
    user_model = get_user_model()
    user_model.objects.create_superuser(callisto_admin_name, callisto_admin_email, callisto_admin_password)


def create_default_space(apps, schema_editor):
    HubSpace = apps.get_model('gallery', 'HubSpace')
    hub_space, created = HubSpace.objects.get_or_create(space_name='Public', type=2)  # SpaceTypes.AllCanWrite
    hub_space.space_description = 'Common space for all authenticated users.'
    hub_space.save()


class Migration(migrations.Migration):
    dependencies = [
        ('gallery', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(generate_superuser),
        migrations.RunPython(create_default_space)
    ]
