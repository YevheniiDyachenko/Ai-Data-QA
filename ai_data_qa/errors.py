from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCategory(StrEnum):
    VALIDATION = "validation"
    SQL_VALIDATION = "sql_validation"
    AI_CONTRACT = "ai_contract"
    CONFIGURATION = "configuration"
    EXECUTION = "execution"
    EXTERNAL_SERVICE = "external_service"
    IO = "io"


class AppError(Exception):
    """Base application exception carrying normalized error metadata."""

    def __init__(
        self,
        message: str,
        *,
        category: ErrorCategory,
        code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.category = category
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "category": self.category,
            "code": self.code,
            "details": self.details,
        }


class SQLValidationError(AppError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.SQL_VALIDATION,
            code="SQL_VALIDATION_ERROR",
            details=details,
        )


class AIContractError(AppError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.AI_CONTRACT,
            code="AI_CONTRACT_ERROR",
            details=details,
        )


class ExecutionError(AppError):
    def __init__(self, message: str, **details: Any) -> None:
        super().__init__(
            message,
            category=ErrorCategory.EXECUTION,
            code="EXECUTION_ERROR",
            details=details,
        )
