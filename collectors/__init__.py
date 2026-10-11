"""
SAMEER Data Ingestion Collectors Package
"""
from collectors.base import BaseCollector
from collectors.firms import FirmsCollector
from collectors.openaq import OpenAQCollector
from collectors.era5 import ERA5Collector
from collectors.cams import CAMSCollector
from collectors.gfas import GFASCollector
from collectors.emissions import EmissionsCollector

__all__ = [
    "BaseCollector",
    "FirmsCollector",
    "OpenAQCollector",
    "ERA5Collector",
    "CAMSCollector",
    "GFASCollector",
    "EmissionsCollector"
]
