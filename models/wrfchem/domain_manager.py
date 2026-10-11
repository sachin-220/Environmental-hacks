"""
WRF/WPS Nested Domain Geometry and Coordinate Grid Manager
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from config.settings import settings


class WRFDomainSpec(BaseModel):
    domain_id: int
    name: str
    grid_spacing_m: float
    parent_id: int
    parent_grid_ratio: int
    i_parent_start: int
    j_parent_start: int
    e_we: int
    e_sn: int
    description: str


class WRFGridHierarchy(BaseModel):
    max_dom: int = 3
    map_proj: str = "lambert"
    ref_lat: float = 28.6139
    ref_lon: float = 77.2090
    truelat1: float = 28.0
    truelat2: float = 32.0
    stand_lon: float = 77.0
    geog_data_res: List[str] = ["default", "default", "default"]
    domains: List[WRFDomainSpec]


def get_default_wrf_domains() -> WRFGridHierarchy:
    """
    Constructs scientifically validated 3-level nested domain configuration
    centered over Delhi NCR and the northern Indian agricultural transport corridor.
    """
    d01 = WRFDomainSpec(
        domain_id=1,
        name="D01_Regional",
        grid_spacing_m=27000.0,
        parent_id=1,
        parent_grid_ratio=1,
        i_parent_start=1,
        j_parent_start=1,
        e_we=46,
        e_sn=46,
        description="Synoptic regional domain covering Punjab, Haryana, Delhi NCR, W-UP, Rajasthan (~1200x1200 km)"
    )

    d02 = WRFDomainSpec(
        domain_id=2,
        name="D02_Intermediate_Transport",
        grid_spacing_m=9000.0,
        parent_id=1,
        parent_grid_ratio=3,
        i_parent_start=12,
        j_parent_start=10,
        e_we=67,
        e_sn=67,
        description="Intermediate plume transport and agricultural fire belt domain (~600x600 km)"
    )

    d03 = WRFDomainSpec(
        domain_id=3,
        name="D03_Delhi_NCR_Inner",
        grid_spacing_m=3000.0,
        parent_id=2,
        parent_grid_ratio=3,
        i_parent_start=22,
        j_parent_start=20,
        e_we=61,
        e_sn=61,
        description="High-resolution inner target domain focused directly on Delhi NCR urban core (~180x180 km)"
    )

    return WRFGridHierarchy(domains=[d01, d02, d03])
