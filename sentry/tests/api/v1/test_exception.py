# -*-coding: utf8 -*-

from sentry.tests.api.v1 import base
from sentry.db import api as dbapi
from sentry.openstack.common import timeutils


class ExceptionAPITests(base.V1AppTest):

    def setUp(self):
        super(ExceptionAPITests, self).setUp()
        self.exception = self._generate_exception()
        self.uuid = self.exception.uuid

    def _generate_exception(self):
        return dbapi.exc_info_detail_create(
            'host1', {}, binary='nova-api', exc_class='ValueError',
            exc_value='ValueError1', file_path='/usr/local/bin/test',
            func_name='testmethod', lineno=100,
            created_at=timeutils.parse_strtime("2013-03-03 01:03:04",
                                               '%Y-%m-%d %H:%M:%S')
        )

    def test_index(self):
        ret = self.app.get('/exceptions')
        self.assertEqual(ret.status_code, 200)

    def test_schema(self):
        ret = self.app.get('/exceptions')
        self.assertEqual(ret.status_code, 200)

    def test_update_note(self):
        note = 'asdfasfasfd'
        ret = self.app.post_json(
            '/exceptions/%s/note' % self.uuid,
            {'note': note},
            expect_errors=True
        )
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.json['exception']['note'], note)

    def test_update_with_invalid_uuid(self):
        uuid = 'ghost-uuid'
        note = 'asdfasfasfd'
        ret = self.app.post_json(
            '/exceptions/%s/note' % uuid,
            {'note': note},
            expect_errors=True
        )
        self.assertEqual(ret.status_code, 404)

    def test_update_with_no_note(self):
        note = 'asdfasfasfd'
        ret = self.app.post_json(
            '/exceptions/%s/note' % self.uuid,
            {'nonote': note},
            expect_errors=True
        )
        self.assertEqual(ret.status_code, 400)

    def test_shutup(self):
        ret = self.app.post_json(
            '/exceptions/shutup',
            {
                "uuids": [self.uuid],
                "start_at": "2013-02-01 11:11:11",
                "end_at": "2013-02-03 00:00:00"
            },
            expect_errors=True
        )
        self.assertEqual(ret.status_code, 200)
        self.assertTrue('exceptions' in ret.json)

    def test_no_shutup(self):
        ret = self.app.post_json(
            '/exceptions/noshutup',
            {
                "uuids": [self.uuid],
            },
            expect_errors=True
        )
        self.assertEqual(ret.status_code, 200)
        self.assertTrue('exceptions' in ret.json)
