"""
Structured Logging Configuration for SAMEER
"""
import logging
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager


class SecretFilter(logging.Filter):
    """Filter that strips accidental API keys or secrets from log messages"""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        # Redact common credential patterns if present
        for pattern in ["key=", "key:", "token=", "token:", "secret=", "password="]:
            if pattern in msg.lower():
                # Sanitize
                record.msg = "[SANITIZED_LOG_MESSAGE_CONTAINING_POSSIBLE_SECRET]"
        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure system-wide logging with structured output"""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger("SAMEER")
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(module)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretFilter())
        root_logger.addHandler(handler)
        
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """Get a named sub-logger under the SAMEER namespace"""
    return logging.getLogger(f"SAMEER.{module_name}")


@contextmanager
def log_operation(logger: logging.Logger, operation: str, **context: Any):
    """
    Context manager to log structured operation lifecycle:
    Records start, duration, record counts, and status/errors.
    """
    start_time = time.perf_counter()
    ctx_str = " | ".join(f"{k}={v}" for k, v in context.items()) if context else ""
    logger.info(f"START operation='{operation}' {ctx_str}".strip())
    status = "SUCCESS"
    error_type: Optional[str] = None
    record_count: Optional[int] = None
    
    try:
        yield lambda count: globals().update(record_count=count) or None
    except Exception as e:
        status = "FAILED"
        error_type = type(e).__name__
        logger.error(f"ERROR in operation='{operation}' error_type='{error_type}' msg='{str(e)}'")
        raise
    finally:
        duration = time.perf_counter() - start_time
        meta = [
            f"operation='{operation}'",
            f"status='{status}'",
            f"duration={duration:.3f}s"
        ]
        if record_count is not None:
            meta.append(f"record_count={record_count}")
        if error_type:
            meta.append(f"error_type='{error_type}'")
        logger.info(f"END {' | '.join(meta)}")
