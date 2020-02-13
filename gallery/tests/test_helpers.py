from django.test import TestCase, RequestFactory
from gallery import helpers
from django.conf import settings
import arrow
from gallery.models import SharedDocument
from gallery.signals import my_handler
from django.contrib.auth import get_user_model


class HelpersTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        self.factory = RequestFactory()
        user_model = get_user_model()
        self.user = user_model.objects.create(username='user1')
        self.user.save()
        self.document = SharedDocument(
            hub_member=self.user,
            document_name='test_notebook.ipynb',
            document_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            published=True
        )
        self.document.save()
        self.user_two = user_model.objects.create(username='user2')
        self.user_two.save()

    def test_document_search(self):
        sources = helpers.find_document_by_keywords('foo', 'data_sources')
        tags = helpers.find_document_by_keywords('foo', 'tags')
        user = helpers.find_document_by_keywords('test', 'user1')
        self.assertEqual(len(sources), 0)
        self.assertEqual(len(tags), 1)
        self.assertEqual(len(user), 1)

    def test_paginator(self):
        queryset = SharedDocument.objects.all().order_by('pk')
        pages = [1, 2, 'NaN']
        for page in pages:
            paginator = helpers.paginate_items(queryset, page)
            self.assertEqual(paginator.number, 1)

    def test_signal_nb_delete(self):
        self.document_two = SharedDocument(
            pk=2,
            hub_member=self.user_two,
            document_name='test_notebook.ipynb',
            document_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            master_document=self.document,
            published=True
        )
        self.document_two.save()
        self.assertEqual(self.document_two.master_document, self.document)
        self.document_three = SharedDocument(
            pk=3,
            hub_member=self.user_two,
            document_name='test_notebook.ipynb',
            document_content=open(
                'gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            master_document=self.document,
            published=True
        )
        self.document_three.save()
        self.assertEqual(self.document_three.master_document, self.document)
        self.document.delete()
        my_handler('SharedDocument', self.document)
        nb_two = SharedDocument.objects.get(pk=2)
        nb_three = SharedDocument.objects.get(pk=3)
        self.assertEqual(nb_three.master_document, nb_two)

    def test_get_all_data_sources_numeric(self):
        sources_numeric = helpers.get_all_data_sources_numeric()
        self.assertIn(('source2', 1), sources_numeric)
        self.assertIn(('source1', 1), sources_numeric)

    def test_get_all_data_sources(self):
        sources = helpers.get_all_data_sources()
        self.assertIn('source2', sources)
        self.assertIn('source1', sources)
