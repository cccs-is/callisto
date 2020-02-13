from django.test import LiveServerTestCase
from selenium import webdriver
import os
from selenium.common.exceptions import NoSuchElementException
from gallery.models import SharedDocument


class LiveSpacesTestCase(LiveServerTestCase):

    fixtures = ['gallery/tests/fixtures/sample_db.json']

    VISIBLE_DOCUMENTS = {
        'd': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_a_backlog',  'schedule_A', 'survey_results_A', 'dept_b_plan',
            'incoming', 'survey_B', 'dept_b_backlog',  'schedule_B', 'survey_results_B'},
        'a': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_b_plan', 'incoming', 'survey_B'},
        'it': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_b_plan', 'incoming', 'survey_B'},
        'ha': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_a_backlog', 'schedule_A', 'survey_results_A', 'dept_b_plan',
            'incoming', 'survey_B', 'survey_results_B'},
        'a1': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_a_backlog', 'schedule_A', 'survey_results_A', 'dept_b_plan',
            'incoming', 'survey_B', 'survey_results_B'},
        'hb': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_b_plan', 'incoming', 'survey_B', 'dept_b_backlog', 'schedule_B',
            'survey_results_B'},
        'b1': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_b_plan', 'incoming', 'survey_B', 'dept_b_backlog', 'schedule_B',
            'survey_results_B'},
        'ab1': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_a_backlog', 'schedule_A', 'survey_results_A', 'dept_b_plan',
            'incoming', 'survey_B', 'dept_b_backlog', 'schedule_B', 'survey_results_B'},
        'int': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_b_plan', 'incoming', 'survey_B', 'gift_exchange'}
    }

    VISIBLE_SPACES = {
        'd': {
            'Department A': ('Read', None),
            'Department A - Confidential': ('Read', None),
            'Department B': ('Read', None),
            'Department B - Confidential': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Admin', 'Edit')
        },
        'a': {
            'Department A': ('Read', None),
            'Department B': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Write', None)
        },
        'it': {
            'Department A': ('Read', 'Edit'),
            'Department A - Confidential': ('None', 'Edit'),
            'Department B': ('Read', 'Edit'),
            'Department B - Confidential': ('None', 'Edit'),
            'Exchange': ('Admin', 'Edit'),
            'WorkFlow': ('Admin', 'Edit')
        },
        'ha': {
            'Department A': ('Admin', 'Edit'),
            'Department A - Confidential': ('Admin', 'Edit'),
            'Department B': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        },
        'a1': {
            'Department A': ('Write', None),
            'Department A - Confidential': ('Write', None),
            'Department B': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        },
        'hb': {
            'Department B': ('Admin', 'Edit'),
            'Department B - Confidential': ('Admin', 'Edit'),
            'Department A': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        },
        'b1': {
            'Department B': ('Write', None),
            'Department B - Confidential': ('Write', None),
            'Department A': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        },
        'ab1': {
            'Department A': ('Write', None),
            'Department A - Confidential': ('Write', None),
            'Department B': ('Write', None),
            'Department B - Confidential': ('Write', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        },
        'int': {
            'Department A': ('Read', None),
            'Department B': ('Read', None),
            'Exchange': ('Write', None),
            'WorkFlow': ('Read', None)
        }
    }

    # user -> document_name -> available_spaces, selected_spaces
    WRITABLE_SPACES = {
        'd': {'hello': ({'Exchange', 'WorkFlow'}, {'WorkFlow'})},
        'a': {'universal_order_form': ({'Exchange', 'WorkFlow'}, {'WorkFlow'}),
              'taxi_wait_time': ({'Exchange', 'WorkFlow'}, {'Exchange'})
              },
        'it': {'ip_and_us': ({'Exchange', 'WorkFlow'}, {'Exchange'})},
        'ha': {'dept_a_plan': ({'Exchange', 'Department A', 'Department A - Confidential'}, {'Department A'}),
              'dept_a_backlog': ({'Exchange', 'Department A', 'Department A - Confidential'}, {'Department A - Confidential'})
              },
        'a1': {'outgoing': ({'Exchange', 'Department A', 'Department A - Confidential'}, {'Department A'}),
               'schedule_A': ({'Exchange', 'Department A', 'Department A - Confidential'}, {'Department A - Confidential'})
              },
        'hb': {'dept_b_plan': ({'Exchange', 'Department B', 'Department B - Confidential'}, {'Department B'}),
               'dept_b_backlog': ({'Exchange', 'Department B', 'Department B - Confidential'}, {'Department B - Confidential'})
              },
        'b1': {'incoming': ({'Exchange', 'Department B', 'Department B - Confidential'}, {'Department B'}),
               'schedule_B': ({'Exchange', 'Department B', 'Department B - Confidential'}, {'Department B - Confidential'})
              },
        'ab1': {'survey_A': ({'Exchange', 'Department A', 'Department A - Confidential', 'Department B', 'Department B - Confidential'}, {'Department A'}),
                'survey_results_A': ({'Exchange', 'Department A', 'Department A - Confidential', 'Department B', 'Department B - Confidential'}, {'Department A - Confidential'}),
                'survey_B': ({'Exchange', 'Department A', 'Department A - Confidential', 'Department B', 'Department B - Confidential'}, {'Department B'}),
                'survey_results_B': ({'Exchange', 'Department A', 'Department A - Confidential', 'Department B', 'Department B - Confidential'}, {'Department A - Confidential', 'Department B - Confidential'})
               },
        'int': {'twin_prime_conjecture': ({'Exchange'}, {'Exchange'}),
                'gift_exchange': ({'Exchange'}, set())
               }
    }

    @classmethod
    def setUpClass(cls):
        super(LiveSpacesTestCase, cls).setUpClass()
        LiveSpacesTestCase.selenium = webdriver.Firefox(executable_path=os.getenv('GECKO_EXECUTABLE'))

    @classmethod
    def tearDownClass(cls):
        LiveSpacesTestCase.selenium.quit()
        super(LiveSpacesTestCase, cls).tearDownClass()

    def _django_login(self, username, password):
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/login/'))
        self.selenium.find_element_by_id('id_username').send_keys(username)
        self.selenium.find_element_by_id('id_password').send_keys(password)
        self.selenium.find_element_by_css_selector('input[type = "submit"]').click()

    def _django_logout(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/admin/logout/'))

    def _get_table_rows(self, table_id):
        table = self.selenium.find_element_by_id(table_id)
        tbody = table.find_element_by_tag_name('tbody')
        return tbody.find_elements_by_tag_name("tr")

    def test_visibility_by_user(self):
        for username, expected_documents in self.VISIBLE_DOCUMENTS.items():
            self._django_login(username, 'password')
            # collect visible documents
            documents = set()
            for page in range(1,3): # If there is only one page we'll get page 1 twice -> ok as results go in set()
                self.selenium.get('%s%s' % (self.live_server_url, '/documents/?page={}'.format(page)))
                rows = self._get_table_rows('document-list-table')
                for row in rows:
                    columns = row.find_elements_by_tag_name("td")
                    code = columns[0].find_element_by_tag_name("code")
                    documents.add(code.text)

            # collect visible spaces
            spaces = {}
            self.selenium.get('%s%s' % (self.live_server_url, '/space/'))
            rows = self._get_table_rows('space-list-table')
            for row in rows:
                columns = row.find_elements_by_tag_name("td")
                space = columns[0].find_element_by_tag_name("code")
                access = columns[1].find_element_by_tag_name("code")
                try:
                    button = columns[2].find_element_by_tag_name("button")
                except NoSuchElementException:
                    button = None
                spaces[space.text]= (access.text, button.text if button else None)

            # writable document spaces
            writable = self.WRITABLE_SPACES.get(username)
            for document_name in writable:
                document = SharedDocument.objects.get(document_name=document_name)
                self.selenium.get('%s%s' % (self.live_server_url, '/edit-document/{}/'.format(document.pk)))
                all_spaces = set()
                selected_spaces = set()
                (expected_all_spaces, expected_selected_spaces) = writable.get(document_name)
                spaces_list = self.selenium.find_element_by_id('spacesList')
                for option in spaces_list.find_elements_by_tag_name("option"):
                    all_spaces.add(option.text)
                    if option.get_attribute("selected"):
                        selected_spaces.add(option.text)
                self.assertSetEqual(all_spaces, expected_all_spaces, "Available document spaces does not match for user {0}, document {1}".format(username, document_name))
                self.assertSetEqual(selected_spaces, expected_selected_spaces, "Selected document spaces does not match for user {0}, document {1}".format(username, document_name))

            self._django_logout()
            self.assertSetEqual(documents, expected_documents)
            self.assertDictEqual(self.VISIBLE_SPACES.get(username), spaces)
