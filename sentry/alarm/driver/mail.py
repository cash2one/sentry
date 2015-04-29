# -*- coding:utf8 -*-
import smtplib
import eventlet
from email.mime import text

from sentry import config
from sentry.alarm.driver import interface
from sentry.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class EmailDriver(interface.BaseAlarmDriver):
    """Sending alarm email driver.

    Only when `smtp_host`, `smtp_username`, `smtp_password` are given, it sends
    email to stmp server, otherwise logging the MIME text content.
    """

    def set_off(self, title, content, **headers):
        LOG.debug("Sending email: '%s'" % title)
        # NOTE(gtt): Yes, each seting off will construct a new object.
        # FIXME: make a connection pool.
        sender = EmailSender(config.get_config('smtp_host'),
                             config.get_config('smtp_username'),
                             config.get_config('smtp_password'),
                             ssl=config.get_config('smtp_ssl'))

        try:
            sender.send(config.get_config('alarm_receivers'), title, content,
                        **headers)
        except Exception:
            LOG.exception('Sending mail: %s failed.' % title)
        else:
            LOG.info("Sending mail: %s successfully." % title)


class EmailSender(object):
    """The real Email implement"""

    def __init__(self, host, username, password, port=0, ssl=True):
        self.host = host
        self.username = username
        self.password = password
        self.use_ssl = ssl
        self.port = port
        self.smtp = None
        self.sender = self._get_sender_name(self.host)

    def _valid_config(self):
        return (self.host and self.username and self.password)

    def _get_sender_name(self, domain):
        suffix = self.host.split('.', 1)[-1]
        return '%s@%s' % (self.username, suffix)

    def connect(self):
        if self.use_ssl:
            self.smtp = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.smtp = smtplib.SMTP(self.host, self.port)

    def login(self):
        try:
            self.smtp.login(self.username, self.password)
        except smtplib.SMTPHeloError:
            raise
        except smtplib.SMTPAuthenticationError:
            raise
        except smtplib.SMTPException:
            raise

    def close(self):
        try:
            self.smtp.close()
        except Exception:
            pass

    def _make_mime(self, to_addrs, title, content, **headers):
        from_addr = self.sender
        mime = text.MIMEText(content, _subtype='html', _charset='utf8')
        mime['Subject'] = title
        mime['From'] = from_addr
        mime['To'] = ';'.join(to_addrs)

        if headers:
            for key, value in headers.iteritems():
                sentry_key = 'X-Sentry-%s' % key.capitalize()
                mime.add_header(sentry_key, value)

        return mime

    def send(self, to_addrs, title, content, **headers):
        """Send email, retries max to 5 times, if failed in the end raises"""

        # NOTE(gtt): Retry 5 times is enougth.
        for retry in xrange(5):
            try:
                from_addr = self.sender
                mime = self._make_mime(to_addrs, title, content, **headers)

                if not self._valid_config():
                    # Fake send
                    LOG.info("'smtp_*' config was not specified, Fake mail.")
                    LOG.info(str(mime))
                else:
                    # Real send
                    self.connect()
                    self.login()
                    self.smtp.sendmail(from_addr, to_addrs, mime.as_string())

                break

            except Exception as ex:
                if retry >= 4:
                    raise

                wait = 2 * retry
                LOG.error('Sending mail: %s failed. Exception: %s, wait %s' %
                          (title, ex, wait))

                eventlet.sleep(wait)
                continue

            finally:
                self.close()
