import json
import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Holds the current request's id; the middleware sets it, the filter reads it so
# every log line emitted during a request is tagged with it.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Logs are written under <project-root>/logs/, anchored to this file's location
# so it works no matter the current working directory.
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "app.log"


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    formatter = JsonFormatter()
    id_filter = RequestIdFilter()

    # console (stdout)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.addFilter(id_filter)

    # rotating file: logs/app.log, up to 5 MB per file, keeping 5 backups
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(id_filter)

    # force=True so we take over the root logger even when uvicorn/gunicorn have
    # already configured logging before the lifespan runs.
    logging.basicConfig(level=level, handlers=[console, file_handler], force=True)

    # Route uvicorn's own loggers through the same handlers.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = [console, file_handler]
        lg.propagate = False
