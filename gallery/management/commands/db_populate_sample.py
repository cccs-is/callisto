from django.core.management.base import BaseCommand
from gallery.models import HubSpace, SpaceTypes


class Command(BaseCommand):
    help = 'Populates database with sample data'

    def hub_space(self, space_name, space_type, space_description):
        hub_space = HubSpace.objects.filter(space_name=space_name).first()
        if hub_space:
            return hub_space
        return HubSpace.objects.create(space_name=space_name, type=space_type.value, space_description=space_description)

    def handle(self, *args, **options):
        self.hub_space('Public', SpaceTypes.AllCanWrite, 'All authenticated users can read and write.')
        self.hub_space('WorkSamples', SpaceTypes.AllCanRead, 'Everybody can read.')
        self.hub_space('Confidential - Department A', SpaceTypes.Private, 'Materials for Department A only.')
        self.hub_space('Confidential - Department B', SpaceTypes.Private, 'Materials for Department B only.')
