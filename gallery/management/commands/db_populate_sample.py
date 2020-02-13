from django.core.management.base import BaseCommand
from gallery.models import HubSpace, SpaceTypes, SharedDocument
from django.contrib.auth import get_user_model

TEST_DOC_CONTENTS = '{"cells": [' + \
  '{ "cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [ { "name": "stdout", "output_type": "stream", "text": [ "Hi" ] } ], "source": [ "print(\'Hi\')" ] },' + \
  '{ "cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": [] }],' + \
  '"metadata": { "kernelspec": { "display_name": "Python 3", "language": "python", "name": "python3" },' + \
  '"language_info": { "codemirror_mode": { "name": "ipython", "version": 3 }, "file_extension": ".py", "mimetype": "text/x-python", "name": "python", "nbconvert_exporter": "python", "pygments_lexer": "ipython3", "version": "3.7.4" } }, "nbformat": 4, "nbformat_minor": 4 }'


class Command(BaseCommand):
    help = 'Populates database with sample data'

    def hub_space(self, space_name, space_type, space_description):
        hub_space = HubSpace.objects.filter(space_name=space_name).first()
        if hub_space:
            return hub_space
        return HubSpace.objects.create(space_name=space_name, type=space_type.value, space_description=space_description)

    def hub_user(self, username, first_name, last_name):
        user_model = get_user_model()
        user = user_model.objects.filter(username=username).first()
        if user:
            return user

        email = first_name + '.' + last_name + '@example.com'
        user = user_model.objects.create_user(username, email, 'password',
            first_name=first_name,
            last_name=last_name,
            is_staff=True)
        return user


    def hub_document(self, document_name, owner, initial_space):
        document = SharedDocument.objects.filter(document_name=document_name).first()
        if document:
            return document
        document = SharedDocument.objects.create(
            hub_member=owner,
            document_name=document_name,
            document_content=TEST_DOC_CONTENTS,
            description="Sample",
            tags='["sample"]',
            data_sources='["None"]',
            published=True)
        if initial_space:
            document.spaces.add(initial_space)
            document.save()
        return document

    def handle(self, *args, **options):
        # create spaces
        space_exchange = self.hub_space('Exchange', SpaceTypes.AllCanWrite, 'All authenticated users can read and write.')
        space_workflow = self.hub_space('WorkFlow', SpaceTypes.AllCanRead, 'Everybody can read.')
        space_dept_a = self.hub_space('Department A', SpaceTypes.AllCanRead, 'Public materials - Department A.')
        space_dept_a_c = self.hub_space('Department A - Confidential', SpaceTypes.Private, 'Materials for Department A use only.')
        space_dept_b = self.hub_space('Department B', SpaceTypes.AllCanRead, 'Public materials - Department B.')
        space_dept_b_c = self.hub_space('Department B - Confidential', SpaceTypes.Private, 'Materials for Department B use only.')

        # create users
        user_d = self.hub_user('d', 'Brian', 'Miller')
        user_a = self.hub_user('a', 'Ashley', 'Clark')
        user_it = self.hub_user('it', 'Peter', 'King')
        user_ha = self.hub_user('ha', 'Lucy', 'Taylor')
        user_a1 = self.hub_user('a1', 'Scott', 'Jackson')
        user_hb = self.hub_user('hb', 'Miles', 'Miller')
        user_b1 = self.hub_user('b1', 'Teresa', 'Williams')
        user_ab1 = self.hub_user('ab1', 'Antonio', 'Johnson')
        user_int = self.hub_user('int', 'Julian', 'Green')

        # make Peter into Callisto Admin
        user_it.is_superuser = True

        # setup access rights
        space_exchange.spaces_admin.add(user_it)

        space_workflow.spaces_admin.add(user_d)
        space_workflow.spaces_admin.add(user_it)
        space_workflow.spaces_write.add(user_d)
        space_workflow.spaces_write.add(user_a)

        space_dept_a.spaces_admin.add(user_ha)
        space_dept_a.spaces_write.add(user_a1)
        space_dept_a.spaces_write.add(user_ab1)

        space_dept_a_c.spaces_admin.add(user_ha)
        space_dept_a_c.spaces_read.add(user_d)
        space_dept_a_c.spaces_write.add(user_a1)
        space_dept_a_c.spaces_write.add(user_ab1)

        space_dept_b.spaces_admin.add(user_hb)
        space_dept_b.spaces_write.add(user_b1)
        space_dept_b.spaces_write.add(user_ab1)

        space_dept_b_c.spaces_admin.add(user_hb)
        space_dept_b_c.spaces_read.add(user_d)
        space_dept_b_c.spaces_write.add(user_b1)
        space_dept_b_c.spaces_write.add(user_ab1)

        # create shared documents
        self.hub_document('taxi_wait_time', user_a, space_exchange)
        self.hub_document('ip_and_us', user_it, space_exchange)
        self.hub_document('twin_prime_conjecture', user_int, space_exchange)

        self.hub_document('hello', user_d, space_workflow)
        self.hub_document('universal_order_form', user_a, space_workflow)

        self.hub_document('dept_a_plan', user_ha, space_dept_a)
        self.hub_document('outgoing', user_a1, space_dept_a)
        self.hub_document('survey_A', user_ab1, space_dept_a)

        self.hub_document('dept_a_backlog', user_ha, space_dept_a_c)
        self.hub_document('schedule_A', user_a1, space_dept_a_c)
        self.hub_document('survey_results_A', user_ab1, space_dept_a_c)

        self.hub_document('dept_b_plan', user_hb, space_dept_b)
        self.hub_document('incoming', user_b1, space_dept_b)
        self.hub_document('survey_B', user_ab1, space_dept_b)

        self.hub_document('dept_b_backlog', user_hb, space_dept_b_c)
        self.hub_document('schedule_B', user_b1, space_dept_b_c)
        survey_results_B = self.hub_document('survey_results_B', user_ab1, space_dept_b_c)
        survey_results_B.spaces.add(space_dept_a_c) # Added into 2 spaces
        survey_results_B.save()

        self.hub_document('gift_exchange', user_int, None)

        # save all spaces
        space_exchange.save()
        space_workflow.save()
        space_dept_a.save()
        space_dept_a_c.save()
        space_dept_b.save()
        space_dept_b_c.save()

        # save all users
        user_d.save()
        user_a.save()
        user_it.save()
        user_ha.save()
        user_a1.save()
        user_hb.save()
        user_b1.save()
        user_ab1.save()
        user_int.save()
