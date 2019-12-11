from django.contrib.auth.models import User
from open_humans.models import OpenHumansMember
import datetime

"""
Temporary code while we switch to a more generic representation
"""


def get_user(unique_name):
    # retrieve or create user
    try:
        django_user = User.objects.get(username=unique_name)
    except User.DoesNotExist:
        django_user = User(username=unique_name)
        django_user.save()

    try:
        ext_user = OpenHumansMember.objects.get(oh_id=unique_name)
    except OpenHumansMember.DoesNotExist:
        ext_user = OpenHumansMember.create(
            oh_id=unique_name,
            oh_username=unique_name,
            access_token='',
            refresh_token='',
            expires_in=31536000.0)  # about 1 year
        ext_user.save()
    return ext_user
