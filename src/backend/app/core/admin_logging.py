
import json
import logging
from collections import deque
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "careerforge-system.jsonl"

MAX_HISTORY = 2000
BACKUP_COUNT = 5

logger = logging.getLogger("careerforge.system")
logger.setLevel(logging.INFO)
logger.propagate = False


def configure_system_logging() -> None:
    if logger.handlers:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    logger.addHandler(handler)


def record_system_event(
    category: str,
    action: str,
    *,
    severity: str = "INFO",
    actor_user_id: int | None = None,
    status_code: int | None = None,
    error_type: str | None = None,
    route: str | None = None,
    duration_ms: float | None = None,
) -> None:
    """
    Record metadata about an application event.

    Do not pass raw request bodies, CV data, credentials,
    access tokens, emails or AI conversations.
    """

    configure_system_logging()

    level = severity.upper()

    if level not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("Unsupported log severity.")

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "severity": level,
        "category": category,
        "action": action,
    }

    if actor_user_id is not None:
        event["actor_user_id"] = actor_user_id

    if status_code is not None:
        event["status_code"] = status_code

    if error_type is not None:
        event["error_type"] = error_type

    if route is not None:
        event["route"] = route
        
    if duration_ms is not None:
        event["duration_ms"] = round(duration_ms, 2)

    logger.log(
        getattr(logging, level),
        json.dumps(event, ensure_ascii=False),
    )


def read_system_events(
    *,
    page: int = 1,
    page_size: int = 25,
    severity: str | None = None,
    category: str | None = None,
) -> dict:
    """
    Read a bounded recent history from active and
    rotated log files. Most recent events come first.
    """

    files = [
        Path(f"{LOG_FILE}.{number}")
        for number in range(BACKUP_COUNT, 0, -1)
    ]

    files.append(LOG_FILE)

    history = deque(maxlen=MAX_HISTORY)

    for file in files:
        if not file.exists():
            continue

        with file.open("r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not isinstance(event, dict):
                    continue

                if (
                    severity
                    and event.get("severity") != severity.upper()
                ):
                    continue

                if (
                    category
                    and event.get("category") != category
                ):
                    continue

                history.append(event)

    events = list(reversed(history))

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "events": events[start:end],
        "page": page,
        "page_size": page_size,
        "window_count": len(events),
        "has_more": end < len(events),
    }
