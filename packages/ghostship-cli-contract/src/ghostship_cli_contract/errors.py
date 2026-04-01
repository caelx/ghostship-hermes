from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CliContractError(Exception):
    exit_code = 10

    def __init__(self, message: str, *, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details

    @property
    def error_type(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "exit_code": self.exit_code,
            }
        }
        if self.details is not None:
            payload["error"]["details"] = self.details
        return payload


class InvalidInputError(CliContractError):
    exit_code = 2


class ConfigError(CliContractError):
    exit_code = 3


class TimeoutError(CliContractError):
    exit_code = 4


@dataclass
class HttpStatusError(CliContractError):
    status_code: int = 0

    def __init__(self, message: str, *, status_code: int, details: Any = None):
        super().__init__(message, details=details)
        self.status_code = status_code
        self.exit_code = 5

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload["error"]["status_code"] = self.status_code
        return payload


class TransportError(CliContractError):
    exit_code = 6


class ResponseDecodeError(CliContractError):
    exit_code = 7


class UnknownCliError(CliContractError):
    exit_code = 10


def exit_code_for_error(error: CliContractError) -> int:
    return error.exit_code
