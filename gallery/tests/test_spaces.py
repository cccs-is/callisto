from django.test import TestCase, RequestFactory, Client
from django.conf import settings
from gallery.models import SharedNotebook, NotebookLike
from gallery.views_notebook_details import render_notebook
import arrow
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

        # TODO make it more precise?

        text_response = str(response.content)
        self.assertContains(response, "Exchange", status_code=200)
        self.assertContains(response, "WorkFlow", status_code=200)
        self.assertContains(response, "Department A", status_code=200)
        self.assertContains(response, "Department B", status_code=200)

        self.assertNotContains(response, "Department A - Confidential", status_code=200)
        self.assertNotContains(response, "Department B - Confidential", status_code=200)
