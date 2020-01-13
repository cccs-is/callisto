from django.test import TestCase, RequestFactory, Client
from django.conf import settings
from gallery.models import SharedNotebook, NotebookLike
from gallery.views_notebook_details import render_notebook
import arrow
import vcr
from django.contrib.auth.models import User


class ViewTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        self.factory = RequestFactory()
        self.user = User(username='ab-1234')
        self.user.save()
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

    def test_notebook_render(self):
        r = self.factory.get('/')
        rendered_notebook = render_notebook(r, self.notebook.id)
        self.assertEqual(rendered_notebook.status_code, 200)
        self.assertIsNotNone(rendered_notebook.content)

    def test_open_notebook(self):
        c = Client()
        self.assertEqual(self.notebook.views, 123)
        c.get('/open-notebook/{}/'.format(self.notebook.id))
        updated_nb = SharedNotebook.objects.get(pk=self.notebook.id)
        self.assertEqual(updated_nb.views, 124)
        c.get('/open-notebook/{}/'.format(self.notebook.id))
        updated_nb = SharedNotebook.objects.get(pk=self.notebook.id)
        self.assertEqual(updated_nb.views, 124)
        c.login(username=self.user.username, password='foobar')
        c.get('/open-notebook/{}/'.format(self.notebook.id))
        self.assertEqual(updated_nb.views, 124)

    def test_shared(self):
        c = Client()
        response = c.get('/shared/')
        self.assertEqual(response.status_code, 200)
        c.login(username=self.user.username, password='foobar')
        logged_in_response = c.get('/shared/')
        self.assertEqual(logged_in_response.status_code, 302)

    def test_index(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
        c.login(username=self.user.username, password='foobar')
        logged_in_response = c.get('/')
        self.assertEqual(logged_in_response.status_code, 302)

    def test_about(self):
        c = Client()
        response = c.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_likes(self):
        c = Client()
        response = c.get('/likes')
        self.assertEqual(response.status_code, 301)
        c.login(username=self.user.username, password='foobar')
        logged_in_response = c.get('/likes/')
        self.assertEqual(logged_in_response.status_code, 200)

    def test_delete_notebook(self):
        c = Client()
        c.login(username=self.user.username, password='foobar')
        self.assertEqual(len(SharedNotebook.objects.all()), 1)
        c.post('/delete-notebook/{}/'.format(self.notebook.pk))
        self.assertEqual(len(SharedNotebook.objects.all()), 0)

    def test_notebook_like(self):
        c = Client()
        c.login(username=self.user.username, password='foobar')
        self.assertEqual(len(NotebookLike.objects.all()), 0)
        c.post('/like-notebook/{}/'.format(self.notebook.pk))
        self.assertEqual(len(NotebookLike.objects.all()), 1)
        c.post('/like-notebook/{}/'.format(self.notebook.pk))
        self.assertEqual(len(NotebookLike.objects.all()), 0)

    @vcr.use_cassette('gallery/tests/fixtures/suggested_sources.yaml',
                      record_mode='none')
    def test_search_notebooks(self):
        c = Client()
        post_response = c.post('/search/', {
                        'search_term': 'source1',
                    })
        self.assertContains(post_response,
                            "test_notebook.ipynb",
                            status_code=200)
        get_response = c.get('/search/', {
                        'search_term': 'source1',
                        'search_field': 'tags'
                    })
        self.assertNotContains(
                get_response,
                "test_notebook.ipynb",
                status_code=200)

    def test_source_index(self):
        c = Client()
        post_response = c.get('/sources/')
        self.assertContains(post_response,
                            "source1",
                            status_code=200)

    def test_notebook_index(self):
        self.second_notebook = SharedNotebook(
            hub_member=self.user,
            notebook_name='second_test.ipynb',
            notebook_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo2", "bar2"]',
            data_sources='["source3", "source4"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format()
        )
        self.second_notebook.save()
        c = Client()
        response = c.get('/notebooks/')
        self.assertContains(response, 'source2', 4, status_code=200)
        response_filtered = c.get('/notebooks/?source=source2')
        self.assertContains(response_filtered, 'source2', status_code=200)
        self.assertContains(response_filtered, 'source3', 2, status_code=200)