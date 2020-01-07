from django.test import TestCase, Client
from django.conf import settings
from gallery.models import SharedNotebook, NotebookComment
import vcr
import arrow
from django.contrib.auth.models import User


class GeneralTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        self.user = User(username='ab-1234')
        self.user.save()

    @vcr.use_cassette('gallery/tests/fixtures/add_notebook.yaml',
                      record_mode='none')
    def test_add_notebook_not_logged_in(self):

        c = Client()
        response = c.post(
            '/add-notebook-gallery/12/',
            {
                'description': 'foobar',
                'tags': 'test, tags',
                'data_sources': 'data,source'
            },
            follow=True)
        self.assertEqual(response.status_code, 200)
        notebooks = SharedNotebook.objects.all()
        self.assertEqual(len(notebooks), 0)

    @vcr.use_cassette('gallery/tests/fixtures/add_notebook.yaml',
                      record_mode='none')
    def test_add_notebook_logged_in(self):

        c = Client()
        c.login(username=self.user.username, password='foobar')
        response = c.post(
            '/add-notebook-gallery/12/',
            {
                'description': 'foobar',
                'tags': 'test, tags',
                'data_sources': 'data,source'
            },
            follow=True)
        self.assertEqual(response.status_code, 200)
        notebooks = SharedNotebook.objects.all()
        self.assertEqual(len(notebooks), 1)
        self.assertEqual(
            notebooks[0].notebook_name,
            'twitter-and-fitbit-activity.ipynb')

    def test_add_comment(self):
        c = Client()
        c.login(username=self.user.username, password='foobar')
        self.assertEqual(len(NotebookComment.objects.all()), 0)
        self.notebook = SharedNotebook(
            hub_member=self.user,
            notebook_name='test_notebook.ipynb',
            notebook_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format()
        )
        self.notebook.save()
        response = c.post(
                    '/add-comment/{}/'.format(self.notebook.id),
                    {'comment_text': 'stupid comment'},
                    follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(NotebookComment.objects.all()), 1)

    def test_edit_notebook(self):
        self.notebook = SharedNotebook(
            hub_member=self.user,
            notebook_name='test_notebook.ipynb',
            notebook_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format()
        )
        self.notebook.save()
        c = Client()
        c.login(username=self.user.username, password='foobar')

        response = c.post(
            '/edit-notebook/{}/'.format(self.notebook.id),
            {
                'description': 'edited',
                'tags': 'notfoo, notbar',
                'data_sources': 'new_data_source',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        updated_nb = SharedNotebook.objects.get(pk=self.notebook.pk)
        self.assertEqual(updated_nb.description, 'edited')
