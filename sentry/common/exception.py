
"""Sentry exception subclasses"""

import urlparse


class RedirectException(Exception):
    def __init__(self, url):
        self.url = urlparse.urlparse(url)


class SentryException(Exception):
    """
    Base Sentry Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    message = _("An unknown exception occurred")

    def __init__(self, message=None, *args, **kwargs):
        if not message:
            message = self.message
        try:
            message = message % kwargs
        except Exception:
            # at least get the core message out if something happened
            pass
        super(SentryException, self).__init__(message)


class MissingArgumentError(SentryException):
    message = _("Missing required argument.")


class MissingCredentialError(SentryException):
    message = _("Missing required credential: %(required)s")


class BadAuthStrategy(SentryException):
    message = _("Incorrect auth strategy, expected \"%(expected)s\" but "
                "received \"%(received)s\"")


class NotFound(SentryException):
    message = _("An object with the specified identifier was not found.")


class UnknownScheme(SentryException):
    message = _("Unknown scheme '%(scheme)s' found in URI")


class BadStoreUri(SentryException):
    message = _("The Store URI was malformed.")


class Duplicate(SentryException):
    message = _("An object with the same identifier already exists.")


class StorageFull(SentryException):
    message = _("There is not enough disk space on the image storage media.")


class StorageWriteDenied(SentryException):
    message = _("Permission to write image storage media denied.")


class AuthBadRequest(SentryException):
    message = _("Connect error/bad request to Auth service at URL %(url)s.")


class AuthUrlNotFound(SentryException):
    message = _("Auth service at URL %(url)s not found.")


class AuthorizationFailure(SentryException):
    message = _("Authorization failed.")


class NotAuthenticated(SentryException):
    message = _("You are not authenticated.")


class Forbidden(SentryException):
    message = _("You are not authorized to complete this action.")


class ForbiddenPublicImage(Forbidden):
    message = _("You are not authorized to complete this action.")


#NOTE(bcwaldon): here for backwards-compatability, need to deprecate.
class NotAuthorized(Forbidden):
    message = _("You are not authorized to complete this action.")


class Invalid(SentryException):
    message = _("Data supplied was not valid.")


class InvalidSortKey(Invalid):
    message = _("Sort key supplied was not valid.")


class InvalidFilterRangeValue(Invalid):
    message = _("Unable to filter using the specified range.")


class AuthorizationRedirect(SentryException):
    message = _("Redirecting to %(uri)s for authorization.")


class DatabaseMigrationError(SentryException):
    message = _("There was an error migrating the database.")


class ClientConnectionError(SentryException):
    message = _("There was an error connecting to a server")


class ClientConfigurationError(SentryException):
    message = _("There was an error configuring the client.")


class MultipleChoices(SentryException):
    message = _("The request returned a 302 Multiple Choices. This generally "
                "means that you have not included a version indicator in a "
                "request URI.\n\nThe body of response returned:\n%(body)s")


class LimitExceeded(SentryException):
    message = _("The request returned a 413 Request Entity Too Large. This "
                "generally means that rate limiting or a quota threshold was "
                "breached.\n\nThe response body:\n%(body)s")

    def __init__(self, *args, **kwargs):
        self.retry_after = (int(kwargs['retry']) if kwargs.get('retry')
                            else None)
        super(LimitExceeded, self).__init__(*args, **kwargs)


class ServiceUnavailable(SentryException):
    message = _("The request returned 503 Service Unavilable. This "
                "generally occurs on service overload or other transient "
                "outage.")

    def __init__(self, *args, **kwargs):
        self.retry_after = (int(kwargs['retry']) if kwargs.get('retry')
                            else None)
        super(ServiceUnavailable, self).__init__(*args, **kwargs)


class ServerError(SentryException):
    message = _("The request returned 500 Internal Server Error.")


class UnexpectedStatus(SentryException):
    message = _("The request returned an unexpected status: %(status)s."
                "\n\nThe response body:\n%(body)s")


class InvalidContentType(SentryException):
    message = _("Invalid content type %(content_type)s")


class BadRegistryConnectionConfiguration(SentryException):
    message = _("Registry was not configured correctly on API server. "
                "Reason: %(reason)s")


class BadStoreConfiguration(SentryException):
    message = _("Store %(store_name)s could not be configured correctly. "
               "Reason: %(reason)s")


class BadDriverConfiguration(SentryException):
    message = _("Driver %(driver_name)s could not be configured correctly. "
               "Reason: %(reason)s")


class StoreDeleteNotSupported(SentryException):
    message = _("Deleting images from this store is not supported.")


class StoreAddDisabled(SentryException):
    message = _("Configuration for store failed. Adding images to this "
               "store is disabled.")


class InvalidNotifierStrategy(SentryException):
    message = _("'%(strategy)s' is not an available notifier strategy.")


class MaxRedirectsExceeded(SentryException):
    message = _("Maximum redirects (%(redirects)s) was exceeded.")


class InvalidRedirect(SentryException):
    message = _("Received invalid HTTP redirect.")


class NoServiceEndpoint(SentryException):
    message = _("Response from Keystone does not contain a Nurse endpoint.")


class RegionAmbiguity(SentryException):
    message = _("Multiple 'image' service matches for region %(region)s. This "
                "generally means that a region is required and you have not "
                "supplied one.")


class WorkerCreationFailure(SentryException):
    message = _("Server worker creation failed: %(reason)s.")


class SchemaLoadError(SentryException):
    message = _("Unable to load schema: %(reason)s")


class InvalidObject(SentryException):
    message = _("Provided object does not match schema "
                "'%(schema)s': %(reason)s")


class UnsupportedHeaderFeature(SentryException):
    message = _("Provided header feature is unsupported: %(feature)s")


class InUseByStore(SentryException):
    message = _("The image cannot be deleted because it is in use through "
                "the backend store outside of Nurse.")


class ImageSizeLimitExceeded(SentryException):
    message = _("The provided image is too large.")


class InvalidInput(Invalid):
    message = _("Invalid input received") + ": %(reason)s"


class ConfigNotFound(SentryException):
    message = _("Could not find config at %(path)s")


class PasteAppNotFound(SentryException):
    message = _("Could not load paste app '%(name)s' from %(path)s")


class NovaclientHelperException(SentryException):
    message = _("Novaclient helper exception occured: %(reason)s")
