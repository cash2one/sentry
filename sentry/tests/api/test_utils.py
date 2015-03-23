from sentry.api import utils
from sentry.api import http_exception
from sentry.tests import test
from sentry.tests.api import fake


class PaginatorTestCase(test.TestCase):

    def test_exceed_max_page(self):
        objs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        pager = utils.Paginator(objs, 1, 5)
        self.assertEqual(pager.total_page_number, 5)

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

    def test_valid_start(self):
        req = fake.fake_request('GET', '/a', 'start=2014-01-01 01:01:01')
        # no raises
        utils.RequestQuery(req)

    def test_invalid_start(self):
        req = fake.fake_request('GET', '/a', 'start=2014x01x01 01:01:01')
        self.assertRaises(http_exception.HTTPBadRequest,
                          utils.RequestQuery, req)

    def test_valid_end(self):
        req = fake.fake_request('GET', '/a', 'end=2014-01-01 01:01:01')
        # no raises
        utils.RequestQuery(req)

    def test_invalid_end(self):
        req = fake.fake_request('GET', '/a', 'end=2014x01x01 01:01:01')
        self.assertRaises(http_exception.HTTPBadRequest,
                          utils.RequestQuery, req)

    def test_passin_sortable_ok(self):
        req = fake.fake_request('GET', '/a', 'sort=xx')
        utils.RequestQuery(req, sortable=['xx'])

        req = fake.fake_request('GET', '/a', 'sort=-xx')
        utils.RequestQuery(req, sortable=['xx'])

    def test_passin_sortable_failed(self):
        req = fake.fake_request('GET', '/a', 'sort=xx')
        self.assertRaises(http_exception.HTTPBadRequest,
                          utils.RequestQuery, req, sortable=['ok'])

    def test_passin_sortable_negative_failed(self):
        req = fake.fake_request('GET', '/a', 'sort=-xx')
        self.assertRaises(http_exception.HTTPBadRequest,
                          utils.RequestQuery, req, sortable=['ok'])

    def test_passin_searchable_ok(self):
        req = fake.fake_request('GET', '/a', 'cat=kitty')
        result = utils.RequestQuery(req, searchable=['cat'])
        self.assertTrue('cat' in result.search_dict)

    def test_passin_searchable_failed(self):
        req = fake.fake_request('GET', '/a', 'cat=kitty')
        self.assertRaises(http_exception.HTTPBadRequest,
                          utils.RequestQuery, req, searchable=['dog'])

    def test_passin_mapper_sort_ok(self):
        req = fake.fake_request('GET', '/a', 'sort=xx')
        result = utils.RequestQuery(req, mapper={'xx': 'yy'})
        self.assertTrue('yy' in result.sort)
        self.assertFalse('xx' in result.sort)

    def test_passin_mapper_negative_sort_ok(self):
        req = fake.fake_request('GET', '/a', 'sort=-xx')
        result = utils.RequestQuery(req, mapper={'xx': 'yy'})
        self.assertTrue('-yy' in result.sort)
        self.assertFalse('-xx' in result.sort)

    def test_passin_mapper_search_ok(self):
        req = fake.fake_request('GET', '/a', 'cat=kitty')
        result = utils.RequestQuery(req, mapper={'cat': 'dog'})
        self.assertTrue('dog' in result.search_dict)
        self.assertFalse('cat' in result.search_dict)
