from django.test import TestCase, RequestFactory, Client
from django.conf import settings
from gallery.models import SharedDocument, HubSpace
from django.contrib.auth import get_user_model


class ViewTest(TestCase):

    fixtures = ['gallery/tests/fixtures/sample_db.json']

    def setUp(self):
        settings.DEBUG = True
        self.factory = RequestFactory()

    def test_spaces_index(self):
        c = Client()
        user_model = get_user_model()
        self.user = user_model.objects.get(username='int')
        c.force_login(self.user)
        response = c.get('/space/')
        self.assertContains(response, 'Julian Green', status_code=200)

        self.assertContains(response, "Exchange", status_code=200)
        self.assertContains(response, "WorkFlow", status_code=200)
        self.assertContains(response, "Department A", status_code=200)
        self.assertContains(response, "Department B", status_code=200)

        self.assertNotContains(response, "Department A - Confidential", status_code=200)
        self.assertNotContains(response, "Department B - Confidential", status_code=200)

    def _direct_document_access(self, client, document_name, should_work):
        document = SharedDocument.objects.get(document_name=document_name)
        response = client.get('/document/{}/'.format(document.pk))
        if should_work:
            self.assertEqual(response.status_code, 200, "Wrong HTTP code for document {}".format(document_name))
        else:
            self.assertRedirects(response, '/', fetch_redirect_response=False)

    def _direct_space_access(self, client, space_name, should_work):
        space = HubSpace.objects.get(space_name=space_name)
        response = client.get('/space/{}/'.format(space.pk))
        if should_work:
            self.assertEqual(response.status_code, 200, "Wrong HTTP code for space {}".format(space_name))
        else:
            self.assertRedirects(response, '/space', fetch_redirect_response=False)

    def test_direct_access(self):
        c = Client()
        user_model = get_user_model()

        # User 'hA' - check direct access to documents and spaces
        ha_user = user_model.objects.get(username='ha')
        c.force_login(ha_user)

        self._direct_document_access(c, 'ip_and_us', True)
        self._direct_document_access(c, 'survey_results_B', True)
        self._direct_document_access(c, 'schedule_B', False)
        self._direct_document_access(c, 'gift_exchange', False)

        self._direct_space_access(c, 'Department A', True)
        self._direct_space_access(c, 'Department B', False)
        c.logout()

        # User 'it' - check direct access to spaces as admin
        it_user = user_model.objects.get(username='it')
        c.force_login(it_user)
        self._direct_space_access(c, 'Exchange', True)
        self._direct_space_access(c, 'Department B - Confidential', True)
        c.logout()
