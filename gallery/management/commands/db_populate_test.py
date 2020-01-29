from django.core.management.base import BaseCommand
from gallery.models import HubSpace, SpaceTypes
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Populates database with test data'

    def _force_create_user(self, index, username_prefix, first_name_prefix, last_name_prefix):
        user_name = username_prefix + str(index)
        user_model = get_user_model()
        user = user_model.objects.filter(username=user_name).first()
        if user:
            user.delete()
        return user_model.objects.create_user(
            username=user_name,
            password='password',
            email=first_name_prefix + '.' + last_name_prefix + str(index) + '@home.com',
            first_name=first_name_prefix + str(index),
            last_name=last_name_prefix + str(index))

    def _force_create_space(self, index, space_name_prefix, space_type):
        space_name = space_name_prefix + str(index)
        hub_space = HubSpace.objects.filter(space_name=space_name).first()
        if hub_space:
            hub_space.delete()
        return HubSpace.objects.create(space_name=space_name, type=space_type.value, space_description='Test Hub Space')

    def _populate(self):
        # create users:
        bunny_users = set()
        scooby_users = set()
        donald_users = set()
        for i in range(50):
            bunny_user = self._force_create_user(i, 'user', 'Bugs', 'Bunny')
            bunny_user.is_staff = True
            bunny_user.save()
            bunny_users.add(bunny_user)
            scooby_user = self._force_create_user(i, 'abc', 'Scooby', 'Doo')
            scooby_users.add(scooby_user)
            donald_user = self._force_create_user(i, 'roo', 'Donald', 'Duck')
            donald_users.add(donald_user)

        # create hub spaces:
        for i in range(10):
            hub_space_private = self._force_create_space(i, 'Private', SpaceTypes.Private)
            hub_space_private.spaces_admin.add(bunny_user)
            hub_space_private.spaces_admin.add(scooby_user)
            hub_space_private.spaces_admin.add(donald_user)
            hub_space_private.spaces_read.set(bunny_users)
            hub_space_private.spaces_write.set(scooby_users)
            hub_space_private.save()

            hub_space_all_read = self._force_create_space(i, 'AllCanRead', SpaceTypes.AllCanRead)
            hub_space_all_read.spaces_admin.add(scooby_user)
            hub_space_all_read.spaces_admin.add(donald_user)
            hub_space_all_read.spaces_write.set(scooby_users)
            hub_space_all_read.save()

            hub_space_all_write = self._force_create_space(i, 'AllCanWrite', SpaceTypes.AllCanWrite)
            hub_space_all_write.spaces_admin.set(donald_users)
            hub_space_all_write.save()

        # TODO create documents in spaces

    def handle(self, *args, **options):
        self._populate()
