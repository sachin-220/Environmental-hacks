"""
Chemical Species and Emission Inventory Mapping Engine for WRF-Chem
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from pydantic import BaseModel

from config.logging_config import get_logger

logger = get_logger("models.wrfchem.emissions_mapping")


class SpeciesMappingRule(BaseModel):
    source_var: str
    target_wrfchem_species: List[str]
    split_fractions: List[float]
    unit_conversion_factor: float
    description: str


class WRFChemEmissionMapper:
    """
    Translates CAMS boundary fields, gridded anthropogenic inventories,
    and satellite FIRMS/GFAS fire detections into standard WRF-Chem chemical species.
    """

    # Molecular weights [g/mol] for conversion between ug/m3 and ppmv
    MW_AIR = 28.97
    MW_O3 = 48.0
    MW_NO2 = 46.01
    MW_SO2 = 64.07
    MW_CO = 28.01

    # VOC Speciation Fractions for South Asian Urban / Road Transport Mixtures
    VOC_SPLIT = {
        "BIGALK": 0.30,   # C4-C5 alkanes
        "BIGENE": 0.15,   # Alkenes
        "TOLUENE": 0.20,  # Toluene / aromatics
        "XYLENE": 0.15,   # Xylenes
        "HCHO": 0.10,     # Formaldehyde
        "CH3CHO": 0.10    # Acetaldehyde
    }

    @classmethod
    def map_cams_to_wrfchem(cls, cams_record: Dict[str, Any], pressure_hpa: float = 1013.25, temp_k: float = 298.15) -> Dict[str, float]:
        """
        Map Copernicus CAMS atmospheric composition variables into WRF-Chem initial/boundary conditions.
        Converts mass concentrations [ug/m3] to mixing ratios [ppmv] where required for gas-phase species.
        """
        wrf_chem_state = {}

        # Molar conversion factor: ppmv = (ug/m3) * (28.97 / MW) * (T / 288.15) * (1013.25 / P) * 1e-3
        def ug_to_ppmv(ug_m3: Optional[float], mw: float) -> float:
            if ug_m3 is None or np.isnan(ug_m3):
                return 0.0
            return (ug_m3 * (cls.MW_AIR / mw) * (temp_k / 288.15) * (1013.25 / pressure_hpa) * 1e-3)

        # 1. Ozone
        if "cams_o3" in cams_record and cams_record["cams_o3"] is not None:
            wrf_chem_state["o3"] = round(ug_to_ppmv(cams_record["cams_o3"], cls.MW_O3), 6)
        
        # 2. NO2 / NO
        if "cams_no2" in cams_record and cams_record["cams_no2"] is not None:
            no2_ppmv = ug_to_ppmv(cams_record["cams_no2"], cls.MW_NO2)
            wrf_chem_state["no2"] = round(no2_ppmv * 0.90, 6)
            wrf_chem_state["no"] = round(no2_ppmv * 0.10, 6)

        # 3. CO (CAMS CO often in mg/m3)
        if "cams_co" in cams_record and cams_record["cams_co"] is not None:
            co_mg = cams_record["cams_co"]
            wrf_chem_state["co"] = round(ug_to_ppmv(co_mg * 1000.0, cls.MW_CO), 6)

        # 4. Particulate Matter (MOSAIC 4-bin aerosol mass breakdown [ug/kg dry air])
        if "cams_pm25" in cams_record and cams_record["cams_pm25"] is not None:
            pm25_val = max(0.0, float(cams_record["cams_pm25"]))
            wrf_chem_state["pm2_5_dry"] = pm25_val
            # Standard MOSAIC chemical distribution for northern India post-monsoon
            wrf_chem_state["so4_a01"] = pm25_val * 0.15
            wrf_chem_state["no3_a01"] = pm25_val * 0.20
            wrf_chem_state["nh4_a01"] = pm25_val * 0.10
            wrf_chem_state["oc_a01"] = pm25_val * 0.35
            wrf_chem_state["bc_a01"] = pm25_val * 0.08
            wrf_chem_state["oin_a01"] = pm25_val * 0.12 # Other inorganics / mineral dust

        return wrf_chem_state

    @classmethod
    def map_anthropogenic_emissions(cls, anthro_record: Dict[str, Any]) -> Dict[str, float]:
        """
        Translate multi-sector gridded inventory rates into WRF-Chem wrfchemi emission flux fields.
        """
        emiss_fields = {}
        
        # NOx split into NO and NO2
        nox = anthro_record.get("anthro_nox", 0.0)
        emiss_fields["E_NO"] = round(nox * 0.90, 4)
        emiss_fields["E_NO2"] = round(nox * 0.10, 4)
        
        emiss_fields["E_SO2"] = round(anthro_record.get("anthro_so2", 0.0), 4)
        emiss_fields["E_CO"] = round(anthro_record.get("anthro_co", 0.0), 4)
        emiss_fields["E_NH3"] = round(anthro_record.get("anthro_nh3", 0.0), 4)
        emiss_fields["E_BC"] = round(anthro_record.get("anthro_bc", 0.0), 4)
        emiss_fields["E_OC"] = round(anthro_record.get("anthro_oc", 0.0), 4)

        # VOC speciation
        voc_total = anthro_record.get("anthro_voc", 0.0)
        for voc_spec, frac in cls.VOC_SPLIT.items():
            emiss_fields[f"E_{voc_spec}"] = round(voc_total * frac, 4)

        return emiss_fields

    @classmethod
    def map_biomass_burning_plume(cls, fire_record: Dict[str, Any]) -> Dict[str, float]:
        """
        Transform FIRMS active fire detection (FRP, coordinates) into WRF-Chem
        wildfire emission injection fluxes and plume rise injection top height.
        """
        frp = max(0.0, float(fire_record.get("frp", 10.0)))
        
        # Freitas et al. empirical plume rise model parameterization
        # z_top [m] estimated from Fire Radiative Power [MW]
        plume_top_m = 180.0 * (frp ** 0.35)
        plume_top_m = float(np.clip(plume_top_m, 100.0, 3500.0))

        # Emission factors for agricultural crop residue burning (Andreae & Merlet)
        # FRP [MW] -> Biomass consumption rate [kg/s] ~ 0.368 * FRP
        biomass_rate_kg_s = 0.368 * frp

        return {
            "fire_frp": frp,
            "plume_top_height_m": round(plume_top_m, 1),
            "fire_pm25_flux_g_s": round(biomass_rate_kg_s * 7.2, 3), # EF ~ 7.2 g/kg
            "fire_co_flux_g_s": round(biomass_rate_kg_s * 68.0, 3),  # EF ~ 68 g/kg
            "fire_nox_flux_g_s": round(biomass_rate_kg_s * 2.5, 3), # EF ~ 2.5 g/kg
            "fire_bc_flux_g_s": round(biomass_rate_kg_s * 0.6, 3),  # EF ~ 0.6 g/kg
            "fire_oc_flux_g_s": round(biomass_rate_kg_s * 3.3, 3)   # EF ~ 3.3 g/kg
        }
