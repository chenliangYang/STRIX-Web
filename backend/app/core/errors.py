"""Custom exceptions."""

from typing import Any


class StrixWebException(Exception):
    """Base exception."""

    def __init__(
        self,
        message: str,
        code: int = 40000,
        data: Any = None,
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)


class BadRequestException(StrixWebException):
    """Bad request exception."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message, code=40000)


class UnauthorizedException(StrixWebException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code=40100)


class ForbiddenException(StrixWebException):
    """Forbidden exception."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code=40300)


class NotFoundException(StrixWebException):
    """Not found exception."""

    def __init__(self, message: str = "Not found"):
        super().__init__(message, code=40400)


class ConflictException(StrixWebException):
    """Conflict exception."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, code=40900)


class TaskStatusNotAllowedException(StrixWebException):
    """Task status not allowed exception."""

    def __init__(self, message: str = "Task status not allowed"):
        super().__init__(message, code=40901)


class WhitelistNotMatchedException(StrixWebException):
    """Whitelist not matched exception."""

    def __init__(self, message: str = "Target not in whitelist"):
        super().__init__(message, code=40902)


class InternalException(StrixWebException):
    """Internal error exception."""

    def __init__(self, message: str = "Internal error"):
        super().__init__(message, code=50000)


class StrixStartFailedException(StrixWebException):
    """STRIX start failed exception."""

    def __init__(self, message: str = "STRIX start failed"):
        super().__init__(message, code=50001)


class StrixStopFailedException(StrixWebException):
    """STRIX stop failed exception."""

    def __init__(self, message: str = "STRIX stop failed"):
        super().__init__(message, code=50002)


class ResultParseFailedException(StrixWebException):
    """Result parse failed exception."""

    def __init__(self, message: str = "Result parse failed"):
        super().__init__(message, code=50003)
