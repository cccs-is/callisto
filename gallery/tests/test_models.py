from django.test import TestCase
from django.conf import settings
from gallery.models import SharedNotebook
from gallery.helpers import identify_master_notebook
import arrow
from django.contrib.auth.models import User


class SharedNotebookTest(TestCase):
    def setUp(self):
        settings.DEBUG = True

        self.user = User(username='ab-1234')
        self.user.save()
        self.notebook = SharedNotebook(
            hub_member=self.user,
            notebook_name='test_notebook.ipynb',
            notebook_content=open('gallery/tests/fixtures/test_notebook.ipynb').read(),
            description='test_description',
            tags='["foo", "bar"]',
            data_sources='["source1", "source2"]',
            views=123,
            updated_at=arrow.now().format(),
            created_at=arrow.now().format()
        )
        self.notebook.save()
        self.user_two = User(username='ab-5678')
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
                    'tags': ['personal data notebook', 'notebook', 'jupyter'],
                    'description': 'A Personal Data Notebook'}
                    }]}

    def test_identify_master_notebook(self):
        mnb = identify_master_notebook(
                'test_notebook.ipynb',
                self.user_two)
        self.assertEqual(mnb, self.notebook)
        no_mnb = identify_master_notebook(
                'edited_test_notebook.ipynb',
                self.user_two)
        self.assertEqual(no_mnb, None)

    def get_notebook_files(self, oh_member_data):
        files = [i for i in oh_member_data['data']
                 if i['source'] == 'direct-sharing-71']
        return files

    def test_get_notebook_files(self):
        nb_files = self.get_notebook_files(self.oh_member_data)
        self.assertEqual(len(nb_files), 1)

    def get_notebook_oh(self, oh_member_data, notebook_id):
        for data_object in oh_member_data['data']:
            if str(data_object['id']) == notebook_id:
                return (data_object['basename'], data_object['download_url'])

    def test_get_notebook_oh(self):
        nbd = self.get_notebook_oh(
            oh_member_data=self.oh_member_data,
            notebook_id='12')
        self.assertEqual(
            nbd,
            ('test_notebook.ipynb', 'http://example.com/test_notebook.ipynb'))

    def test_metadata_functions(self):
        self.assertEqual(self.notebook.get_tags(),
                         'foo,bar')
        self.assertEqual(self.notebook.get_data_sources(),
                         'source1,source2')
