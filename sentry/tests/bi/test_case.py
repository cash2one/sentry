from sentry.tests import test
from sentry.bi import engine as bi_engine
from sentry.bi import case as bi_case


class InstanceCreateTest(test.TestCase):

    def setUp(self):
        super(InstanceCreateTest, self).setUp()
        self.case = bi_case.InstanceCreateStart()
        self.snapshot_bi_name = 'compute.instance.create.from.snapshot'
        self.image_bi_name = 'compute.instance.create.from.image'

    def test_fill_bi_name_dup_create_from_image(self):
        action = bi_engine.Action()
        action.bi_name = self.image_bi_name
        self.case.fill_bi_name(action, 'new_name')
        self.assertEqual(action.bi_name, self.image_bi_name)

    def test_fill_bi_name_dup_create_from_snapshot(self):
        action = bi_engine.Action()
        action.bi_name = self.snapshot_bi_name
        self.assertRaises(bi_case.TaggerError,
                          self.case.fill_bi_name, action, 'new_name')

    def test_fill_bi_name_ok(self):
        action = bi_engine.Action()
        self.case.fill_bi_name(action, 'new_name')
        self.assertEqual(action.bi_name, 'new_name')

    def test_snapshot(self):
        message = {
            'event_type': 'compute.instance.create.start',
            'payload': {
                'image_meta': {
                    'image_type': 'snapshot',
                }
            }
        }
        self.assertEqual(self.snapshot_bi_name,
                         self.case._get_bi_name(message))

    def test_image_type_no_value(self):
        message = {
            'event_type': 'compute.instance.create.start',
            'payload': {
                'image_meta': {
                    'image_type': '',
                }
            }
        }
        self.assertEqual(self.image_bi_name,
                         self.case._get_bi_name(message))

    def test_no_image_type(self):
        message = {
            'event_type': 'compute.instance.create.start',
            'payload': {
                'image_meta': {
                }
            }
        }
        self.assertEqual(self.image_bi_name,
                         self.case._get_bi_name(message))

    def test_no_image_meta(self):
        message = {
            'event_type': 'compute.instance.create.start',
            'payload': {}
        }
        self.assertEqual(self.image_bi_name,
                         self.case._get_bi_name(message))
