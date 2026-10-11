"""
SAMEER Configuration and Domain Specification
"""
import os
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DomainBounds(BaseModel):
    """Bounding box in decimal degrees (WGS84)"""
    west: float = Field(..., description="Western longitude")
    south: float = Field(..., description="Southern latitude")
    east: float = Field(..., description="Eastern longitude")
    north: float = Field(..., description="Northern latitude")

    def contains(self, lat: float, lon: float) -> bool:
        return (self.south <= lat <= self.north) and (self.west <= lon <= self.east)


class DomainGridConfig(BaseModel):
    """Domain resolution and boundary specification"""
    domain_id: str
    name: str
    resolution_km: float
    bounds: DomainBounds
    source_resolution_note: str = ""


class Settings(BaseSettings):
    """Global system configuration for SAMEER"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Operating Mode
    SAMEER_MODE: Literal["live", "demo"] = Field(
        default="demo",
        description="Operating mode: 'live' uses online APIs, 'demo' uses local cached/sample datasets"
    )

    # Logging
    SAMEER_LOG_LEVEL: str = Field(default="INFO", description="Log level")

    # API Credentials
    FIRMS_MAP_KEY: Optional[str] = Field(default=None, description="NASA FIRMS MAP Key")
    OPENAQ_API_KEY: Optional[str] = Field(default=None, description="OpenAQ v3 API Key")
    CDS_API_KEY: Optional[str] = Field(default=None, description="Copernicus CDS API Key")

    # SMTP Email Configuration
    EMAIL_ADDRESS: Optional[str] = Field(default=None, description="Sender email address for alerts")
    EMAIL_PASSWORD: Optional[str] = Field(default=None, description="App password for SMTP sender")
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    # Generative AI Configuration
    GENAI_API_KEY: Optional[str] = Field(default=None, description="Generative AI API Key for real-time citizen guidance")

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    DATA_FINAL_DIR: Path = BASE_DIR / "data" / "final"
    DATASETS_SAMPLE_DIR: Path = BASE_DIR / "DATASETS"

    # Regional Study Domain: Punjab, Haryana, Delhi NCR, western UP, parts of Rajasthan
    REGIONAL_DOMAIN: DomainBounds = DomainBounds(
        west=73.5,
        south=27.0,
        east=78.5,
        north=32.5
    )

    # Delhi NCR Core Focus Target (Reference center at Connaught Place / Central Delhi)
    DELHI_CENTER_LAT: float = 28.6139
    DELHI_CENTER_LON: float = 77.2090

    # Delhi NCR Urban Core Inner Domain (D03 3-km Airshed)
    DELHI_NCR_DOMAIN: DomainBounds = DomainBounds(
        west=76.8,
        south=28.2,
        east=77.6,
        north=28.9
    )

    # Active Target Ingestion Domain: "delhi_ncr" or "regional"
    TARGET_DOMAIN: str = Field(
        default="delhi_ncr",
        description="Active domain for collectors: 'delhi_ncr' or 'regional'"
    )

    @property
    def active_domain(self) -> DomainBounds:
        """Returns the active bounding box based on TARGET_DOMAIN setting"""
        if str(self.TARGET_DOMAIN).lower() in ("delhi_ncr", "delhi", "ncr", "d03"):
            return self.DELHI_NCR_DOMAIN
        return self.REGIONAL_DOMAIN

    # Nested Grid Hierarchy
    # D01: Regional Parent Domain (~27 km)
    # D02: Intermediate Agricultural / Transport Belt (~9 km)
    # D03: High-Resolution Delhi NCR Inner Core (~3 km)
    NESTED_DOMAINS: List[DomainGridConfig] = [
        DomainGridConfig(
            domain_id="D01",
            name="Regional Domain (Punjab, Haryana, Delhi NCR, W-UP)",
            resolution_km=27.0,
            bounds=DomainBounds(west=73.5, south=27.0, east=78.5, north=32.5),
            source_resolution_note="Interpolated from ~0.25 deg ERA5 reanalysis and ~0.4 deg CAMS"
        ),
        DomainGridConfig(
            domain_id="D02",
            name="Intermediate Inflow Domain",
            resolution_km=9.0,
            bounds=DomainBounds(west=75.5, south=27.5, east=78.0, north=31.0),
            source_resolution_note="Intermediate grid mapping for upwind agricultural plume transport"
        ),
        DomainGridConfig(
            domain_id="D03",
            name="Delhi NCR Urban Core Inner Domain",
            resolution_km=3.0,
            bounds=DomainBounds(west=76.8, south=28.2, east=77.6, north=28.9),
            source_resolution_note="High-resolution inner target grid for urban exposure and intervention modeling"
        )
    ]

    # Pressure levels (hPa) for vertical profile & inversion diagnostics
    PRESSURE_LEVELS_HPA: List[int] = [1000, 950, 925, 900, 850, 700, 500]

    # Pollutant parameters monitored
    POLLUTANTS: List[str] = ["pm25", "pm10", "o3", "no2", "so2", "co"]

    # Ingestion rate limits & timeouts
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5

    def get_masked_credentials(self) -> dict:
        """Return credentials with tokens safely masked for logging & inspection"""
        def mask(val: Optional[str]) -> str:
            if not val or val.startswith("YOUR_") or val == "demo_firms_key" or val == "demo_openaq_key" or val == "demo_cds_key":
                return "[NOT CONFIGURED / DEMO]"
            if len(val) <= 8:
                return "***"
            return f"{val[:3]}...{val[-3:]}"

        return {
            "MODE": self.SAMEER_MODE,
            "FIRMS_MAP_KEY": mask(self.FIRMS_MAP_KEY),
            "OPENAQ_API_KEY": mask(self.OPENAQ_API_KEY),
            "CDS_API_KEY": mask(self.CDS_API_KEY),
        }

    def validate_live_credentials(self) -> List[str]:
        """Check for missing credentials when running in live mode"""
        missing = []
        if self.SAMEER_MODE == "live":
            if not self.FIRMS_MAP_KEY or self.FIRMS_MAP_KEY.startswith("YOUR_") or self.FIRMS_MAP_KEY == "demo_firms_key":
                missing.append("FIRMS_MAP_KEY")
            if not self.OPENAQ_API_KEY or self.OPENAQ_API_KEY.startswith("YOUR_") or self.OPENAQ_API_KEY == "demo_openaq_key":
                missing.append("OPENAQ_API_KEY")
            if not self.CDS_API_KEY or self.CDS_API_KEY.startswith("YOUR_") or self.CDS_API_KEY == "demo_cds_key":
                missing.append("CDS_API_KEY")
        return missing


settings = Settings()
