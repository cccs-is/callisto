from django.test import LiveServerTestCase
from selenium import webdriver
import os
from selenium.common.exceptions import NoSuchElementException


class LiveSpacesTestCase(LiveServerTestCase):

    fixtures = ['gallery/tests/fixtures/sample_db.json']

    VISIBLE_NOTEBOOKS = {
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
            'incoming', 'survey_B', 'dept_b_backlog'},
        'a1': {
            'taxi_wait_time', 'ip_and_us', 'twin_prime_conjecture', 'hello', 'universal_order_form', 'dept_a_plan',
            'outgoing', 'survey_A', 'dept_a_backlog', 'schedule_A', 'survey_results_A', 'dept_b_plan',
            'incoming', 'survey_B', 'dept_b_backlog'},
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
        for username, expected_notebooks in self.VISIBLE_NOTEBOOKS.items():
            self._django_login(username, 'password')
            # collect visible notebooks
            notebooks = set()
            for page in range(1,3): # If there is only one page we'll get page 1 twice -> ok as results go in set()
                self.selenium.get('%s%s' % (self.live_server_url, '/notebooks/?page={}'.format(page)))
                rows = self._get_table_rows('notebook-list-table')
                for row in rows:
                    columns = row.find_elements_by_tag_name("td")
                    code = columns[0].find_element_by_tag_name("code")
                    notebooks.add(code.text)

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

            self._django_logout()
            self.assertSetEqual(notebooks, expected_notebooks)
            self.assertDictEqual(self.VISIBLE_SPACES.get(username), spaces)
