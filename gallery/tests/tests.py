from django.test import TestCase, Client
from django.conf import settings
from gallery.models import SharedDocument, DocumentComment
import arrow
from django.contrib.auth import get_user_model


class GeneralTest(TestCase):
    def setUp(self):
        settings.DEBUG = True
        user_model = get_user_model()
        self.user = user_model.objects.create(username='ab-1234')
        self.user.save()

    def test_add_notebook_not_logged_in(self):
        c = Client()
        response = c.post(
            '/nbupload/',
            {
                'document_name': 'twitter-and-fitbit-activity.ipynb',
                'notebook_contents': open('gallery/tests/fixtures/test_notebook.ipynb').read()
            },
            follow=True)
        self.assertEqual(response.status_code, 401)
        documents = SharedDocument.objects.all()
        self.assertEqual(len(documents), 0)

    def test_add_notebook_logged_in(self):
        c = Client()
        c.force_login(self.user)
        response = c.post(
            '/nbupload/',
            {
                'document_name': 'twitter-and-fitbit-activity.ipynb',
                'notebook_contents': open('gallery/tests/fixtures/test_notebook.ipynb').read()
            },
            follow=True)
        self.assertEqual(response.status_code, 200)
        documents = SharedDocument.objects.all()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].document_name, 'twitter-and-fitbit-activity.ipynb')

    def test_add_comment(self):
        c = Client()
        c.force_login(self.user)
        self.assertEqual(len(DocumentComment.objects.all()), 0)
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
        response = c.post(
                    '/add-comment/{}/'.format(self.document.id),
                    {'comment_text': 'stupid comment'},
                    follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(DocumentComment.objects.all()), 1)

    def test_edit_notebook(self):
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
        c = Client()
        c.force_login(self.user)

        response = c.post(
            '/edit-document/{}/'.format(self.document.id),
            {
                'description': 'edited',
                'tags': 'notfoo, notbar',
                'data_sources': 'new_data_source',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        updated_nb = SharedDocument.objects.get(pk=self.document.pk)
        self.assertEqual(updated_nb.description, 'edited')
