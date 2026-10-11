"""
WRF-Chem Coupled and Control Namelist Generator and Serializer
"""
from pathlib import Path
from typing import Optional, List
import pandas as pd

from models.wrfchem.domain_manager import WRFGridHierarchy, get_default_wrf_domains
from models.wrfchem.chemistry_config import WRFChemCoupledConfig, MECHANISM_MOZART_MOSAIC
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("models.wrfchem.wrf_namelist_builder")


class WRFNamelistBuilder:
    """Constructs, validates, and serializes namelist.input for WRF-Chem coupled and control runs"""

    def __init__(
        self,
        grid_hierarchy: Optional[WRFGridHierarchy] = None,
        chem_config: Optional[WRFChemCoupledConfig] = None
    ):
        self.grid = grid_hierarchy or get_default_wrf_domains()
        self.chem = chem_config or WRFChemCoupledConfig()

    def generate_namelist_content(
        self,
        start_date: str = "2023-11-01_00:00:00",
        end_date: str = "2023-11-04_00:00:00",
        time_step: int = 90, # Fundamental time step for D01 in seconds
        history_interval_min: int = 60, # 1-hour output frequency for canonical alignment
        is_coupled: bool = True
    ) -> str:
        """
        Generate strict Fortran format namelist.input string for WRF-Chem
        """
        d = self.grid
        max_dom = d.max_dom
        
        # Parse dates
        start_dt = pd.to_datetime(start_date.replace("_", " "))
        end_dt = pd.to_datetime(end_date.replace("_", " "))
        duration_days = (end_dt - start_dt).days
        duration_hours = int((end_dt - start_dt).total_seconds() // 3600) % 24

        s_years = ", ".join([str(start_dt.year)] * max_dom)
        s_months = ", ".join([f"{start_dt.month:02d}"] * max_dom)
        s_days = ", ".join([f"{start_dt.day:02d}"] * max_dom)
        s_hours = ", ".join([f"{start_dt.hour:02d}"] * max_dom)
        
        e_years = ", ".join([str(end_dt.year)] * max_dom)
        e_months = ", ".join([f"{end_dt.month:02d}"] * max_dom)
        e_days = ", ".join([f"{end_dt.day:02d}"] * max_dom)
        e_hours = ", ".join([f"{end_dt.hour:02d}"] * max_dom)

        e_wes = ", ".join(str(dom.e_we) for dom in d.domains)
        e_sns = ", ".join(str(dom.e_sn) for dom in d.domains)
        e_verts = ", ".join(["40"] * max_dom) # 40 vertical sigma levels
        
        dx_str = str(int(d.domains[0].grid_spacing_m))
        dy_str = str(int(d.domains[0].grid_spacing_m))
        
        parent_ids = ", ".join(str(dom.parent_id) for dom in d.domains)
        parent_ratios = ", ".join(str(dom.parent_grid_ratio) for dom in d.domains)
        i_starts = ", ".join(str(dom.i_parent_start) for dom in d.domains)
        j_starts = ", ".join(str(dom.j_parent_start) for dom in d.domains)
        parent_time_step_ratios = ", ".join(str(dom.parent_grid_ratio) for dom in d.domains)

        feedback_val = 1 if is_coupled else 0
        chem_opt_val = self.chem.mechanism.chem_opt

        content = f"""&time_control
 run_days                            = {duration_days},
 run_hours                           = {duration_hours},
 run_minutes                         = 0,
 run_seconds                         = 0,
 start_year                          = {s_years},
 start_month                         = {s_months},
 start_day                           = {s_days},
 start_hour                          = {s_hours},
 end_year                            = {e_years},
 end_month                           = {e_months},
 end_day                             = {e_days},
 end_hour                            = {e_hours},
 interval_seconds                    = 21600,
 input_from_file                     = .true., .true., .true.,
 history_interval                    = {history_interval_min}, {history_interval_min}, {history_interval_min},
 frames_per_outfile                  = 1, 1, 1,
 restart                             = .false.,
 restart_interval                    = 1440,
 io_form_history                     = 2,
 io_form_restart                     = 2,
 io_form_input                       = 2,
 io_form_boundary                    = 2,
/

&domains
 time_step                           = {time_step},
 time_step_fract_num                 = 0,
 time_step_fract_den                 = 1,
 max_dom                             = {max_dom},
 e_we                                = {e_wes},
 e_sn                                = {e_sns},
 e_vert                              = {e_verts},
 p_top_requested                     = 5000,
 num_metgrid_levels                  = 38,
 num_metgrid_soil_levels             = 4,
 dx                                  = {dx_str}, {int(dx_str)//3}, {int(dx_str)//9},
 dy                                  = {dy_str}, {int(dy_str)//3}, {int(dy_str)//9},
 grid_id                             = 1, 2, 3,
 parent_id                           = {parent_ids},
 i_parent_start                      = {i_starts},
 j_parent_start                      = {j_starts},
 parent_grid_ratio                   = {parent_ratios},
 parent_time_step_ratio              = {parent_time_step_ratios},
 feedback                            = 1,
 smooth_option                       = 0,
/

&physics
 mp_physics                          = 10, 10, 10,
 ra_lw_physics                       = 4, 4, 4,
 ra_sw_physics                       = 4, 4, 4,
 radt                                = 15, 5, 2,
 sf_sfclay_physics                   = 1, 1, 1,
 sf_surface_physics                  = 2, 2, 2,
 bl_pbl_physics                      = 1, 1, 1,
 bldt                                = 0, 0, 0,
 cu_physics                          = 1, 1, 0,
 cudt                                = 5, 5, 0,
 isfflx                              = 1,
 ifsnow                              = 1,
 icloud                              = 1,
 surface_input_source                = 3,
 num_soil_layers                     = 4,
 sf_urban_physics                    = 1, 1, 1,
/

&chem
 chem_opt                            = {chem_opt_val}, {chem_opt_val}, {chem_opt_val},
 chem_in_opt                         = 1, 1, 1,
 phot_opt                            = 2, 2, 2,
 gas_chem                            = 1, 1, 1,
 aerchem                             = 1, 1, 1,
 aer_ra_feedback                     = {feedback_val}, {feedback_val}, {feedback_val},
 aer_op_opt                          = 1, 1, 1,
 gas_drydep_opt                      = 1, 1, 1,
 aer_drydep_opt                      = 1, 1, 1,
 bio_emiss_opt                       = 3, 3, 3,
 emiss_opt                           = 8, 8, 8,
 biomass_burn_opt                    = 1, 1, 1,
 plumerisefire_frq                   = 30, 30, 30,
 have_bcs_chem                       = .true., .true., .true.,
 chemdt                              = 0, 0, 0,
/

&dynamics
 w_damping                           = 1,
 diff_opt                            = 1, 1, 1,
 km_opt                              = 4, 4, 4,
 damp_opt                            = 3,
 base_temp                           = 290.,
 zdamp                               = 5000., 5000., 5000.,
 dampcoef                            = 0.2, 0.2, 0.2,
 khdif                               = 0, 0, 0,
 kvdif                               = 0, 0, 0,
 non_hydrostatic                     = .true., .true., .true.,
/

&bdy_control
 spec_bdy_width                      = 5,
 spec_zone                           = 1,
 relax_zone                          = 4,
 specified                           = .true., .false., .false.,
 nested                              = .false., .true., .true.,
/

&namelist_quilt
 nio_tasks_per_group = 0,
 nio_groups = 1,
/
"""
        return content

    def write_coupled_namelist(self, output_path: Path, **kwargs) -> Path:
        """Write coupled namelist (aer_ra_feedback=1)"""
        content = self.generate_namelist_content(is_coupled=True, **kwargs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote WRF-Chem COUPLED namelist (aer_ra_feedback=1) to {output_path}")
        return output_path

    def write_control_namelist(self, output_path: Path, **kwargs) -> Path:
        """Write control namelist (aer_ra_feedback=0)"""
        content = self.generate_namelist_content(is_coupled=False, **kwargs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote WRF-Chem CONTROL namelist (aer_ra_feedback=0) to {output_path}")
        return output_path
