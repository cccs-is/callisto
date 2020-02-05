from gallery.models import HubSpace
import logging

logger = logging.getLogger(__name__)


def spaces_read(hub_member):
    spaces = HubSpace.objects.all()
    result = set()
    for space in spaces:
        if space.can_read(hub_member):
            result.add(space)
    return result


def spaces_write(hub_member):
    spaces = HubSpace.objects.all()
    result = set()
    for space in spaces:
        if space.can_write(hub_member):
            result.add(space)
    return result


def spaces_admin(hub_member):
    spaces = HubSpace.objects.all()
    result = set()
    for space in spaces:
        if space.can_admin(hub_member):
            result.add(space)
    return result
