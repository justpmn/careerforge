
import logging

from functools import wraps
from time import perf_counter
from typing import Awaitable, Callable, ParamSpec, TypeVar

import httpx

from src.backend.app.core.admin_logging import record_system_event


P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)


def _record_event(
    action: str,
    severity: str,
    duration_ms: float,
    error_type: str | None = None,
    status_code: int | None = None,
) -> None:
    """
    Record AI Mentor operational telemetry.

    Never record prompts, conversations, CV content,
    model responses or user credentials.

    Logging failure must not interrupt the AI Mentor.
    """

    try:
        record_system_event(
            category="ai_mentor",
            action=action,
            severity=severity,
            error_type=error_type,
            status_code=status_code,
            duration_ms=duration_ms,
        )

    except Exception:
        logger.exception(
            "Failed to record AI Mentor telemetry."
        )


def monitor_mentor_inference(
    function: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[T]]:
    """
    Measure AI Mentor request duration and failures.

    Preserves the wrapped function's return value
    and exception behavior.
    """

    @wraps(function)
    async def wrapper(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        started = perf_counter()

        try:
            result = await function(*args, **kwargs)

        except Exception as error:
            duration_ms = (
                perf_counter() - started
            ) * 1000

            cause = error.__cause__ or error

            status_code = None

            if isinstance(
                cause,
                httpx.TimeoutException,
            ):
                action = "mentor_inference_timeout"
                severity = "WARNING"

            elif isinstance(
                cause,
                httpx.HTTPStatusError,
            ):
                action = "mentor_provider_http_error"
                severity = "ERROR"
                status_code = (
                    cause.response.status_code
                )

            elif isinstance(
                cause,
                httpx.RequestError,
            ):
                action = "mentor_connection_failed"
                severity = "ERROR"

            elif isinstance(error, ValueError):
                action = "mentor_request_rejected"
                severity = "WARNING"

            else:
                action = "mentor_inference_failed"
                severity = "ERROR"

            _record_event(
                action=action,
                severity=severity,
                duration_ms=duration_ms,
                error_type=type(cause).__name__,
                status_code=status_code,
            )

            # Preserve the existing error behavior.
            raise

        else:
            duration_ms = (
                perf_counter() - started
            ) * 1000

            _record_event(
                action="mentor_inference_completed",
                severity="INFO",
                duration_ms=duration_ms,
            )

            return result

    return wrapper
