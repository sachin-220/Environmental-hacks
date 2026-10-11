"""
Base Collector Interface for SAMEER Data Ingestion Layer
"""
import time
import abc
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import requests
from config.settings import settings
from config.logging_config import get_logger, log_operation

logger = get_logger("collectors.base")


class BaseCollector(abc.ABC):
    """Abstract base class for all environmental and meteorological data collectors"""

    def __init__(self, source_name: str, raw_subfolder: str):
        self.source_name = source_name
        self.raw_dir = settings.DATA_RAW_DIR / raw_subfolder
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    @property
    def mode(self) -> str:
        return settings.SAMEER_MODE

    @abc.abstractmethod
    def fetch_live(self, start_date: str, end_date: str, **kwargs) -> pd.DataFrame:
        """Execute online network request to fetch real-time or historical data from official API"""
        pass

    @abc.abstractmethod
    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached raw data or synthetic demo dataset pack when in DEMO mode or offline"""
        pass

    def collect(self, start_date: Optional[str] = None, end_date: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Unified collector entrypoint: cleanly dispatches between LIVE and DEMO mode
        and guarantees scientific integrity and transparent provenance.
        """
        with log_operation(logger, f"collect_{self.source_name}", mode=self.mode):
            if self.mode == "live":
                missing = self.validate_credentials()
                if missing:
                    msg = (
                        f"Collector '{self.source_name}' cannot run in LIVE mode. "
                        f"Missing required environment credentials: {', '.join(missing)}. "
                        f"Set these in your .env file or switch SAMEER_MODE=demo."
                    )
                    logger.warning(msg)
                    logger.info(f"Falling back to local cached/demo dataset for '{self.source_name}'")
                    return self.load_cached_or_demo(**kwargs)
                try:
                    df = self.fetch_live(start_date=start_date or "", end_date=end_date or "", **kwargs)
                    return df
                except Exception as e:
                    logger.error(f"Failed to fetch live data from {self.source_name}: {e}. Falling back to cache.")
                    return self.load_cached_or_demo(**kwargs)
            else:
                logger.info(f"Running in DEMO mode: loading cached/sample data for '{self.source_name}'")
                return self.load_cached_or_demo(**kwargs)

    @abc.abstractmethod
    def validate_credentials(self) -> List[str]:
        """Return list of missing credentials needed for this collector"""
        pass

    def _http_get_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = settings.REQUEST_TIMEOUT_SECONDS
    ) -> requests.Response:
        """Perform robust HTTP GET request with retries and exponential backoff"""
        retries = settings.MAX_RETRIES
        backoff = settings.RETRY_BACKOFF_FACTOR
        
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
                if response.status_code == 429: # Rate limit
                    wait_time = int(response.headers.get("Retry-After", backoff * attempt))
                    logger.warning(f"Rate limited by {self.source_name}. Waiting {wait_time}s (attempt {attempt}/{retries})")
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return response
            except (requests.RequestException, Exception) as e:
                logger.warning(f"HTTP request to {url} failed on attempt {attempt}/{retries}: {e}")
                if attempt == retries:
                    raise
                time.sleep(backoff ** attempt)
        raise RuntimeError(f"Exceeded max retries for {url}")
