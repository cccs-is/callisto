from django.test import TestCase, RequestFactory
from gallery import helpers
from django.conf import settings
import arrow
from gallery.models import SharedNotebook
from gallery.signals import my_handler
from django.contrib.auth import get_user_model


class HelpersTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        self.factory = RequestFactory()
        user_model = get_user_model()
        self.user = user_model.objects.create(username='user1')
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
            created_at=arrow.now().format(),
            published=True
        )
        self.notebook.save()
        self.user_two = user_model.objects.create(username='user2')
        self.user_two.save()

    def test_notebook_search(self):
        sources = helpers.find_notebook_by_keywords('foo', 'data_sources')
        tags = helpers.find_notebook_by_keywords('foo', 'tags')
        user = helpers.find_notebook_by_keywords('test', 'user1')
        self.assertEqual(len(sources), 0)
        self.assertEqual(len(tags), 1)
        self.assertEqual(len(user), 1)

    def test_paginator(self):
        queryset = SharedNotebook.objects.all().order_by('pk')
        pages = [1, 2, 'NaN']
        for page in pages:
            paginator = helpers.paginate_items(queryset, page)
            self.assertEqual(paginator.number, 1)

    def test_signal_nb_delete(self):
        self.notebook_two = SharedNotebook(
            pk=2,
            hub_member=self.user_two,
            notebook_name='test_notebook.ipynb',
            notebook_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            master_notebook=self.notebook,
            published=True
        )
        self.notebook_two.save()
        self.assertEqual(self.notebook_two.master_notebook, self.notebook)
        self.notebook_three = SharedNotebook(
            pk=3,
            hub_member=self.user_two,
            notebook_name='test_notebook.ipynb',
            notebook_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            master_notebook=self.notebook,
            published=True
        )
        self.notebook_three.save()
        self.assertEqual(self.notebook_three.master_notebook, self.notebook)
        self.notebook.delete()
        my_handler('SharedNotebook', self.notebook)
        nb_two = SharedNotebook.objects.get(pk=2)
        nb_three = SharedNotebook.objects.get(pk=3)
        self.assertEqual(nb_three.master_notebook, nb_two)

    def test_get_all_data_sources_numeric(self):
        sources_numeric = helpers.get_all_data_sources_numeric()
        self.assertIn(('source2', 1), sources_numeric)
        self.assertIn(('source1', 1), sources_numeric)

    def test_get_all_data_sources(self):
        sources = helpers.get_all_data_sources()
        self.assertIn('source2', sources)
        self.assertIn('source1', sources)
