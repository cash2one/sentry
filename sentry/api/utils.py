from math import ceil
from functools import partial
from oslo.config import cfg

from sentry.api import bottle
from sentry.api import http_exception
from sentry.openstack.common import timeutils
from sentry.openstack.common import jsonutils


CONF = cfg.CONF
# 100 pages
MAX_PAGE = 100


def create_bottle_app(autojson=False, catchall=False):
    pretty_jsondumps = partial(jsonutils.dumps, indent=4)
    app = bottle.Bottle(autojson=autojson, catchall=catchall)
    app.install(bottle.JSONPlugin(pretty_jsondumps))
    return app


class Paginator(object):
    def __init__(self, object_list, per_page, max_page=MAX_PAGE):
        """
        :para object_list: should be a list or QuerySet.
        """
        self.object_list = object_list
        self.per_page = per_page
        self.max_count = per_page * max_page

        self._count = None
        self._total_page_number = None

    @property
    def count(self):
        if self._count is None:
            try:
                # NOTE(gtt): Accounting all row is very slow.
                # Like jd.com and taobao.com only return max to 100 pages.
                # Here we do the same. If 100 pages doesn't contain expected
                # information, you should use more filters.
                self._count = self.object_list.limit(self.max_count).count()
            except (AttributeError, TypeError):
                self._count = len(self.object_list)
                if self._count > self.max_count:
                    self._count = self.max_count
        return self._count

    @property
    def total_page_number(self):
        if self._total_page_number is None:
            if self.count == 0:
                self._total_page_number = 0
            else:
                self._total_page_number = int(ceil(self.count /
                                                   float(self.per_page)))

        return self._total_page_number

    def validate_number(self, number):
        """
        Validates the given 1-based page number.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise ValueError('That page number is not an integer')
        if number < 1:
            raise ValueError('That page number is less than 1')
        if number > self.total_page_number:
                raise ValueError('That page contains no results')
        return number

    def page(self, page_num):
        if self.count == 0:
            return Page([], page_num, self.total_page_number,
                        self.per_page, self.count)

        page_num = self.validate_number(page_num)
        bottom = (page_num - 1) * self.per_page
        top = bottom + self.per_page
        if top > self.count:
            top = self.count

        p = Page(self.object_list[bottom: top],
                 page_num, self.total_page_number, self.per_page, self.count)
        return p


class Page(object):

    def __init__(self, object_list, page_num, total_page, per_page,
                 total_count):
        self.object_list = object_list
        self.page_num = page_num
        self.total_page = total_page
        self.per_page = per_page
        self.total_count = total_count

    def to_dict(self):
        ret = {
            'pagination': {
                "total_page": self.total_page,
                "current_page": self.page_num,
                "limit": self.per_page,
            }
        }
        return ret

    def __iter__(self):
        for obj in self.object_list:
            yield obj


class RequestQuery(object):

    def __init__(self, request, mapper=None, sortable=None, searchable=None):
        """
        Parse uri like `/?sort=a,-b&page=1&limit=100&col1=value1&col2=value2`
        """
        self.request = request
        query_dict = dict(request.query.allitems())
        self._query_dict = query_dict

        sort = query_dict.pop('sort', None)
        if sort:
            self._sort = sort.split(',')
        else:
            self._sort = []
        self._validate_sortable(sortable)
        self._normalize_sort(mapper)

        self._page_num = int(query_dict.pop('page', 1))
        self._limit = int(query_dict.pop('limit', CONF.api.default_items))

        self.start = query_dict.pop('start', None)
        if self.start:
            self.validate_timestr(self.start)

        self.end = query_dict.pop('end', None)
        if self.end:
            self.validate_timestr(self.end)

        self._search_dict = query_dict
        self._validate_searchable(searchable)
        self._normalize_search_dict(mapper)

    def _validate_sortable(self, sortable):
        if sortable is None:
            return

        for sort in self._sort:
            if sort[0] == '-':
                sort = sort[1:]

            if sort not in sortable:
                msg = ('field: %s is not in sortable fields: %s' %
                       (sort, sortable))
                raise http_exception.HTTPBadRequest(msg)

    def _validate_searchable(self, searchable):
        if searchable is None:
            return

        for field in self._search_dict.keys():
            if field not in searchable:
                msg = ('field: %s is not in searchable fields: %s' %
                       (field, searchable))
                raise http_exception.HTTPBadRequest(msg)

    def _normalize_sort(self, mapper):
        if mapper is None:
            return

        new_sort = []
        for sort in self._sort:
            neg = False

            if sort[0] == '-':
                sort = sort[1:]
                neg = True

            new_item = mapper.get(sort, sort)
            if not neg:
                new_sort.append(new_item)
            else:
                new_sort.append('-%s' % new_item)
        self._sort = new_sort

    def _normalize_search_dict(self, mapper):
        if mapper is None:
            return

        normalized_search_dict = {}
        for key, value in self._search_dict.iteritems():
            new_key = mapper.get(key, key)
            normalized_search_dict[new_key] = value
        self._search_dict = normalized_search_dict

    def validate_timestr(self, timestr, local=True):
        try:
            if local:
                return timeutils.parse_local_isotime(timestr)
            else:
                return timeutils.parse_isotime(timestr)
        except ValueError:
            msg = '%s not in valid iso8601 format' % timestr
            raise http_exception.HTTPBadRequest(msg)

    @property
    def sort(self):
        """
        Return a list. If not specifiy sort, return a empty list.
        Multiple sort given, return the latest.

        .e.g ['a', '-b']
        """
        return self._sort

    @property
    def page_num(self):
        """
        Return the page num (int), if multiple page given, return the latest
        Default is 1.
        """
        return self._page_num

    @property
    def limit(self):
        """
        return int limit, if multiple limit given return the latest
        """
        return self._limit

    @property
    def search_dict(self):
        """
        return a dict like {"col1": "value1", "col2": "volue2"}
        """
        return self._search_dict

    def search_get_int(self, key, default):
        try:
            return int(self.search_dict.get(key, default))
        except ValueError:
            return default

    def json_get(self, key, default=None):
        """Get the key from jsonable body.

        If key is not existed in body, and default is given, then return
        the default, otherwise raise http_exceptions.
        """
        try:
            if not self.request.json:
                msg = ('No body. Are you miss header "'
                    'content-type: application/json"')
                raise http_exception.HTTPBadRequest(msg)
        except ValueError:
            msg = ('Invalid json body')
            raise http_exception.HTTPBadRequest(msg)

        try:
            return self.request.json[key]
        except KeyError:
            if default:
                return default
            else:
                msg = "%s must given." % key
                raise http_exception.HTTPBadRequest(msg)
