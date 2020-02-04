from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Temporary manual test for missing user name'

    def handle(self, *args, **options):
        user_name = 'test-no-name'
        user_model = get_user_model()
        user = user_model.objects.filter(username=user_name).first()
        if user:
            user.delete()
        user_model.objects.create_user(
            username=user_name,
            password='password',
            email='test@home.com',
            first_name='',  # None,
            last_name='')  # None)
            #first_name=None,
            #last_name=None)
