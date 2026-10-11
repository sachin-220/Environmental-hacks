"""
WRF-Chem Chemical Mechanisms, Aerosol Schemes, and Physics Coupling Specifications
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ChemicalMechanismSpec(BaseModel):
    chem_opt: int
    name: str
    gas_mechanism: str
    aerosol_mechanism: str
    photolysis_scheme: str
    aerosol_optical_option: int
    feedback_supported: bool
    description: str


# Scientifically validated WRF-Chem chemistry options
MECHANISM_MOZART_MOSAIC = ChemicalMechanismSpec(
    chem_opt=108,
    name="MOZART-MOSAIC_4bin",
    gas_mechanism="MOZART (Model for Ozone and Related chemical Tracers)",
    aerosol_mechanism="MOSAIC (Model for Simulating Aerosol Interactions and Chemistry) 4-bin with Aqueous Chemistry",
    photolysis_scheme="Fast-J photolysis (phot_opt=2)",
    aerosol_optical_option=1,
    feedback_supported=True,
    description="State-of-the-art coupled gas-aerosol mechanism representing detailed secondary organic aerosols, sulfate-nitrate-ammonium thermodynamics, and direct aerosol-radiation coupling."
)

MECHANISM_RADM2_MADE = ChemicalMechanismSpec(
    chem_opt=202,
    name="RADM2-MADE/SORGAM",
    gas_mechanism="RADM2 (Regional Acid Deposition Model version 2)",
    aerosol_mechanism="MADE/SORGAM (Modal Aerosol Dynamics Model for Europe / Secondary Organic Aerosol Model)",
    photolysis_scheme="Fast-J photolysis (phot_opt=2)",
    aerosol_optical_option=1,
    feedback_supported=True,
    description="Robust modal aerosol mechanism supporting direct radiative feedback and modal aerosol size distribution (Aitken, accumulation, coarse)."
)


class WRFPhysicsConfig(BaseModel):
    mp_physics: int = 10         # Morrison 2-moment microphysics (supports aerosol-cloud interactions)
    ra_lw_physics: int = 4       # RRTMG Longwave Radiation
    ra_sw_physics: int = 4       # RRTMG Shortwave Radiation
    radt: int = 15               # Radiation call frequency [minutes]
    sf_sfclay_physics: int = 1   # Revised MM5 Surface Layer Scheme
    sf_surface_physics: int = 2  # Unified Noah Land-Surface Model
    bl_pbl_physics: int = 1      # Yonsei University (YSU) Planetary Boundary Layer Scheme
    bldt: int = 0                # PBL call frequency (every step)
    cu_physics: int = 1          # Kain-Fritsch cumulus (active on D01, off on D03)


class WRFChemCoupledConfig(BaseModel):
    mechanism: ChemicalMechanismSpec = MECHANISM_MOZART_MOSAIC
    physics: WRFPhysicsConfig = WRFPhysicsConfig()
    aer_ra_feedback: int = 1     # 1 = Two-way direct aerosol-radiation feedback enabled; 0 = Control / Off
    aer_op_opt: int = 1          # Aerosol optical properties calculated dynamically from aerosol mass/size
    phot_opt: int = 2            # Fast-J photolysis
    gas_drydep_opt: int = 1      # Wesely gas dry deposition
    aer_drydep_opt: int = 1      # Aerosol dry deposition
    bio_emiss_opt: int = 3       # MEGAN biogenic emissions
    biomass_burn_opt: int = 1    # Wildfire plume rise model (FRE/FRP driven)
    plumerisefire_frq: int = 30  # Call plume rise every 30 min
    emiss_opt: int = 8           # Gridded anthropogenic emissions
    chem_in_opt: int = 1         # Read chemical IC/BCs from wrfinput and wrfbdy
    gas_chem: int = 1            # Gas chemistry enabled
    aerchem: int = 1             # Aerosol chemistry enabled
