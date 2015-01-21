from sentry.api import utils
from sentry.tests import test
from sentry.tests.api import fake


class PaginatorTestCase(test.TestCase):
    def test_no_count(self):
        objs = []
        pager = utils.Paginator(objs, 1)
        self.assertEqual(pager.count, 0)
        self.assertEqual(pager.total_page_number, 0)
        self.assertEqual(pager.page(1).object_list, [])

    def test_count_correctly1(self):
        # even object list
        objs = ['a', 'b']
        pager = utils.Paginator(objs, 1)
        self.assertEqual(pager.count, 2)
        self.assertEqual(pager.total_page_number, 2)

        pager = utils.Paginator(objs, 2)
        self.assertEqual(pager.count, 2)
        self.assertEqual(pager.total_page_number, 1)

    def test_count_correctly2(self):
        # odd object
        objs = ['a', 'b', 'c']
        pager = utils.Paginator(objs, 1)
        self.assertEqual(pager.count, 3)
        self.assertEqual(pager.total_page_number, 3)

        pager = utils.Paginator(objs, 2)
        self.assertEqual(pager.count, 3)
        self.assertEqual(pager.total_page_number, 2)

    def test_page(self):
        objs = ['a', 'b', 'c', 'd', 'e']
        pager = utils.Paginator(objs, 2)
        page1 = pager.page(1)
        page2 = pager.page(2)

        self.assertEqual(page1.total_page, 3)
        self.assertEqual(page1.page_num, 1)
        self.assertEqual(page1.per_page, 2)
        self.assertEqual(page1.total_count, 5)

        self.assertEqual(page1.object_list, ['a', 'b'])
        self.assertEqual(page2.object_list, ['c', 'd'])

    def test_invalid_page(self):
        objs = ['a', 'b', 'c', 'd', 'e']
        pager = utils.Paginator(objs, 2)

        self.assertRaises(ValueError, pager.page, 300)
        self.assertRaises(ValueError, pager.page, -100)
        self.assertRaises(ValueError, pager.page, 0)


class RequestQueryTestCase(test.TestCase):

    def test_1(self):
        request = fake.fake_request('GET', '/a', '')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, [])
        self.assertEqual(query.page_num, 1)
        self.assertEqual(query.limit, 20)
        self.assertEqual(query.search_dict, {})

    def test_no_sort(self):
        request = fake.fake_request('GET', '/a', 'limit=1')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, [])

    def test_one_sort(self):
        request = fake.fake_request('GET', '/a', 'sort=1')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, ['1'])

    def test_two_sort(self):
        request = fake.fake_request('GET', '/a', 'sort=1,-2')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, ['1', '-2'])

    def test_dup_sort(self):
        request = fake.fake_request('GET', '/a', 'sort=1&sort=2')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, ['2'])

    def test_invalid_sort(self):
        request = fake.fake_request('GET', '/a', 'sort=1.|2')
        query = utils.RequestQuery(request)

        self.assertEqual(query.sort, ['1.|2'])

    def test_limit(self):
        request = fake.fake_request('GET', '/a', 'limit=10')

        query = utils.RequestQuery(request)
        self.assertEqual(query.limit, 10)

    def test_dup_limit(self):
        request = fake.fake_request('GET', '/a', 'limit=10&limit=20')

        query = utils.RequestQuery(request)
        self.assertEqual(query.limit, 20)

    def test_invalid_limit(self):
        request = fake.fake_request('GET', '/a', 'limit=x20')

        self.assertRaises(ValueError, utils.RequestQuery, request)

    def test_page(self):
        request = fake.fake_request('GET', '/a', 'page=20')

        query = utils.RequestQuery(request)
        self.assertEqual(query.page_num, 20)

    def test_dup_page(self):
        request = fake.fake_request('GET', '/a', 'page=20&page=10')

        query = utils.RequestQuery(request)
        self.assertEqual(query.page_num, 10)

    def test_invalid_page(self):
        request = fake.fake_request('GET', '/a', 'page=ax1')

        self.assertRaises(ValueError, utils.RequestQuery, request)

    def test_negetive_page(self):
        request = fake.fake_request('GET', '/a', 'page=-20')

        query = utils.RequestQuery(request)
        self.assertEqual(query.page_num, -20)

    def test_search(self):
        request = fake.fake_request('GET', '/a', 'sort=1&a=b')
        query = utils.RequestQuery(request)
        self.assertEqual(query.search_dict, {'a': 'b'})

        request = fake.fake_request('GET', '/a', 'sort=1&1=2&c=d')
        query = utils.RequestQuery(request)
        self.assertEqual(query.search_dict, {'1': '2', 'c': 'd'})
