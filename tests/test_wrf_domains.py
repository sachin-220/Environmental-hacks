"""
Unit tests for WRF/WPS nested domain geometries and projection parameters
"""
import pytest
from models.wrfchem.domain_manager import (
    WRFGridHierarchy,
    WRFDomainSpec,
    get_default_wrf_domains
)


def test_default_wrf_domains():
    grid = get_default_wrf_domains()
    assert grid.max_dom == 3
    assert grid.map_proj == "lambert"
    assert grid.ref_lat == 28.6139
    assert grid.ref_lon == 77.2090
    assert len(grid.domains) == 3

    d01, d02, d03 = grid.domains
    
    # Domain 1 (Regional)
    assert d01.domain_id == 1
    assert d01.grid_spacing_m == 27000.0
    assert d01.parent_grid_ratio == 1
    
    # Domain 2 (Intermediate)
    assert d02.domain_id == 2
    assert d02.grid_spacing_m == 9000.0
    assert d02.parent_id == 1
    assert d02.parent_grid_ratio == 3
    
    # Domain 3 (Delhi NCR Inner)
    assert d03.domain_id == 3
    assert d03.grid_spacing_m == 3000.0
    assert d03.parent_id == 2
    assert d03.parent_grid_ratio == 3

    # Boundary safety checks
    assert d02.i_parent_start + (d02.e_we // 3) <= d01.e_we
    assert d02.j_parent_start + (d02.e_sn // 3) <= d01.e_sn
    assert d03.i_parent_start + (d03.e_we // 3) <= d02.e_we
    assert d03.j_parent_start + (d03.e_sn // 3) <= d02.e_sn
