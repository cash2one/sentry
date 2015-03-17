import datetime

from sentry.openstack.common import log as logging
from sentry.openstack.common import lockutils

LOG = logging.getLogger(__name__)


class Action(object):
    """Lean class store information about a user action."""

    MAX_AGE_SECONDS = 86400  # One day

    def __init__(self):
        self.bi_name = None
        self.request_id = None
        self.start_at = None
        self.end_at = None
        self.tenant_id = None
        self.tenant_name = None
        self.identifier = None
        self.start_message = None
        self._birth_day = datetime.datetime.now()

    def old_enough(self):
        delta = datetime.datetime.now() - self._birth_day
        return delta.seconds >= self.MAX_AGE_SECONDS

    @property
    def finished(self):
        return self.end_at is not None

    def __repr__(self):
        return '<Action %s>' % self.request_id


class BIAnalyzer(object):
    """The core BI Engine.

    Passin every notification to me. I will using tagger to fill these
    requests. I use `Action()` to modeling user requests. When an Action() is
    finished, I calling callback() method, which in common is logging to BI.

    I also trim actions that leave for a long time (24 hours).
    """

    def __init__(self, taggers, callback):
        """
        :param taggers: A list of `Tagger` object.
        :param callback: A callable object, when a request finished,
                         I will calling `callback()` passin action object.
        """
        # key is event_type, value is tagger object.
        self.taggers = {}

        # key is request_id, value is action object.
        self.actions = {}

        self.callback = callback

        for tagger in taggers:
            self.register_tagger(tagger)

    def register_tagger(self, tagger):
        if tagger.event_type in self.taggers:
            raise ValueError("duplicate tagger %s" % tagger)

        LOG.debug("Register BI tagger: %s" % tagger.event_type)
        self.taggers[tagger.event_type] = tagger

    def get_tagger(self, event_type):
        # NOTE(gtt): Do *NOT* insert new key into taggers
        if event_type in self.taggers.keys():
            return self.taggers[event_type]
        else:
            return None

    def process(self, message):
        try:
            request_id = message['_context_request_id']
            event_type = message['event_type']
        except KeyError as ex:
            LOG.warn("%s raises %s" % (message, ex))
            return

        action = self._get_or_create_action(request_id)

        tagger = self.get_tagger(event_type)

        if tagger:
            LOG.debug("Using tagger: %s to process: %s" % (tagger, action))
            tagger.tag(action, message)

            if action.finished:
                self.callback(action)
                self._remove_action(action)

        self._clean_old_action()
        # if not tagger, ignore this event

    @lockutils.synchronized('bi_action', 'sentry_bi')
    def _get_or_create_action(self, request_id):
        return self.actions.setdefault(request_id, Action())

    @lockutils.synchronized('bi_action', 'sentry_bi')
    def _remove_action(self, action):
        self.actions.pop(action.request_id, None)

    @lockutils.synchronized('bi_action', 'sentry_bi')
    def _clean_old_action(self):
        """Some error action there is no end event, so clean up old action."""

        INTERVAL = 60  # 1 minute
        if hasattr(self, '_last_cleanup'):
            now = datetime.datetime.now()
            delta = now - self._last_cleanup
            if delta.seconds < INTERVAL:
                return

        LOG.debug("Clean up old actions")
        setattr(self, '_last_cleanup', datetime.datetime.now())

        for key, action in self.actions.iteritems():
            if action.old_enough():

                if action.start_at is not None:
                    LOG.exception("Cleanup started %s" % action)

                self.actions.pop(key)
