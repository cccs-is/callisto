from django.test import TestCase, RequestFactory, Client
from django.conf import settings
from gallery.models import SharedNotebook, HubSpace
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

    def _direct_notebook_access(self, client, notebook_name, should_work):
        notebook = SharedNotebook.objects.get(notebook_name=notebook_name)
        response = client.get('/notebook/{}/'.format(notebook.pk))
        if should_work:
            self.assertEqual(response.status_code, 200, "Wrong HTTP code for notebook {}".format(notebook_name))
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

        # User 'hA' - check direct access to notebooks and spaces
        ha_user = user_model.objects.get(username='ha')
        c.force_login(ha_user)

        self._direct_notebook_access(c, 'ip_and_us', True)
        self._direct_notebook_access(c, 'survey_results_B', True)
        self._direct_notebook_access(c, 'schedule_B', False)
        self._direct_notebook_access(c, 'gift_exchange', False)

        self._direct_space_access(c, 'Department A', True)
        self._direct_space_access(c, 'Department B', False)
        c.logout()

        # User 'it' - check direct access to spaces as admin
        it_user = user_model.objects.get(username='it')
        c.force_login(it_user)
        self._direct_space_access(c, 'Exchange', True)
        self._direct_space_access(c, 'Department B - Confidential', True)
        c.logout()
