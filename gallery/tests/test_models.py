from django.test import TestCase
from django.conf import settings
from gallery.models import SharedDocument
from gallery.helpers import identify_master_document
import arrow
from django.contrib.auth import get_user_model


class SharedDocumentTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        user_model = get_user_model()
        self.user = user_model.objects.create(username='ab-1234')
        self.user.save()
        self.document = SharedDocument(
            hub_member=self.user,
            document_name='test_notebook.ipynb',
            document_content=open('gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format(),
            published=True
        )
        self.document.save()
        self.user_two = user_model.objects.create(username='ab-5678')
        self.user_two.save()
        self.oh_member_data = {
            'created': '2018-01-19T21:55:40.049169Z',
            'next': None,
            'project_member_id': '1234',
            'message_permission': True,
            'sources_shared': ['direct-sharing-71'],
            'username': 'gedankenstuecke',
            'data': [{
                'id': 12,
                'source': 'direct-sharing-71',
                'basename': 'test_notebook.ipynb',
                'created': '2018-06-06T17:09:26.688794Z',
                'download_url': 'http://example.com/test_notebook.ipynb',
                'metadata': {
                    'tags': ['personal data document', 'document', 'jupyter'],
                    'description': 'A Personal Data Notebook'}
                    }]}

    def test_identify_master_document(self):
        mnb = identify_master_document('test_notebook.ipynb', self.user_two)
        self.assertEqual(mnb, self.document)
        no_mnb = identify_master_document('edited_test_notebook.ipynb', self.user_two)
        self.assertEqual(no_mnb, None)

    def test_metadata_functions(self):
        self.assertEqual(self.document.get_tags(), 'foo,bar')
        self.assertEqual(self.document.get_data_sources(), 'source1,source2')
