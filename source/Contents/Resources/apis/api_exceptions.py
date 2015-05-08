class Unauthorized(Exception):
    pass


class NotAllowed(Exception):
    pass


class UserNotFound(Exception):
    pass


class RateLimited(Exception):
    pass


class ServerError(Exception):
    pass


class ServiceUnavailable(Exception):
    pass