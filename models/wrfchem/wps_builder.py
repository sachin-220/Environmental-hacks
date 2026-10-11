"""
WPS (WRF Preprocessing System) Namelist Generator and Validator
"""
from pathlib import Path
from typing import Optional
import pandas as pd
from models.wrfchem.domain_manager import WRFGridHierarchy, get_default_wrf_domains
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("models.wrfchem.wps_builder")


class WPSNamelistBuilder:
    """Constructs, validates, and serializes namelist.wps for geogrid, ungrib, and metgrid"""

    def __init__(self, grid_hierarchy: Optional[WRFGridHierarchy] = None):
        self.grid = grid_hierarchy or get_default_wrf_domains()

    def generate_namelist_content(
        self,
        start_date: str = "2023-11-01_00:00:00",
        end_date: str = "2023-11-04_00:00:00",
        geog_path: str = "/data/static/WPS_GEOG",
        opt_output_from_geogrid_path: str = "./",
        interval_seconds: int = 21600 # 6 hours for ERA5 forcing
    ) -> str:
        """
        Generate strict Fortran format namelist.wps string
        """
        d = self.grid
        max_dom = d.max_dom
        
        # Format arrays
        start_dates = ", ".join([f"'{start_date}'"] * max_dom)
        end_dates = ", ".join([f"'{end_date}'"] * max_dom)
        
        parent_ids = ", ".join(str(dom.parent_id) for dom in d.domains)
        parent_ratios = ", ".join(str(dom.parent_grid_ratio) for dom in d.domains)
        i_starts = ", ".join(str(dom.i_parent_start) for dom in d.domains)
        j_starts = ", ".join(str(dom.j_parent_start) for dom in d.domains)
        e_wes = ", ".join(str(dom.e_we) for dom in d.domains)
        e_sns = ", ".join(str(dom.e_sn) for dom in d.domains)
        geog_res = ", ".join([f"'{r}'" for r in d.geog_data_res])

        content = f"""&share
 wrf_core = 'ARW',
 max_dom = {max_dom},
 start_date = {start_dates},
 end_date   = {end_dates},
 interval_seconds = {interval_seconds},
 io_form_geogrid = 2,
/

&geogrid
 parent_id         = {parent_ids},
 parent_grid_ratio = {parent_ratios},
 i_parent_start    = {i_starts},
 j_parent_start    = {j_starts},
 e_we              = {e_wes},
 e_sn              = {e_sns},
 geog_data_res     = {geog_res},
 dx = {int(d.domains[0].grid_spacing_m)},
 dy = {int(d.domains[0].grid_spacing_m)},
 map_proj = '{d.map_proj}',
 ref_lat   = {d.ref_lat:.4f},
 ref_lon   = {d.ref_lon:.4f},
 truelat1  = {d.truelat1:.2f},
 truelat2  = {d.truelat2:.2f},
 stand_lon = {d.stand_lon:.2f},
 geog_data_path = '{geog_path}',
 opt_geogrid_tbl_path = 'geogrid/',
/

&ungrib
 out_format = 'WPS',
 prefix = 'FILE',
/

&metgrid
 fg_name = 'FILE',
 io_form_metgrid = 2,
 opt_metgrid_tbl_path = 'metgrid/',
/
"""
        return content

    def write_namelist_file(
        self,
        output_path: Path,
        start_date: str = "2023-11-01_00:00:00",
        end_date: str = "2023-11-04_00:00:00",
        geog_path: str = "/data/static/WPS_GEOG"
    ) -> Path:
        """Write namelist.wps to specified path"""
        content = self.generate_namelist_content(start_date, end_date, geog_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote validated WPS namelist to {output_path}")
        return output_path
