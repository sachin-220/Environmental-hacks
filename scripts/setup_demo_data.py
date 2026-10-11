"""
Setup Demo and Sample Data Script for SAMEER
Generates and populates local cache directories and DATASETS folder
for offline demonstration and robust testing.
"""
import sys
import math
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("scripts.setup_demo_data")


def generate_demo_datasets():
    """Create comprehensive synthetic demo dataset pack covering Delhi NCR domain"""
    datasets_dir = settings.DATASETS_SAMPLE_DIR
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Ground Air Quality (01_ground_air_quality.csv)
    stations = [
        {"station_id": "DEL001", "station_name": "Anand Vihar, Delhi", "latitude": 28.6476, "longitude": 77.3158},
        {"station_id": "DEL002", "station_name": "R K Puram, Delhi", "latitude": 28.5632, "longitude": 77.1869},
        {"station_id": "DEL003", "station_name": "Punjabi Bagh, Delhi", "latitude": 28.6740, "longitude": 77.1310},
        {"station_id": "DEL004", "station_name": "ITO, Delhi", "latitude": 28.6289, "longitude": 77.2410},
        {"station_id": "DEL005", "station_name": "Dwarka Sector 8, Delhi", "latitude": 28.5710, "longitude": 77.0719},
        {"station_id": "DEL006", "station_name": "Jahangirpuri, Delhi", "latitude": 28.7328, "longitude": 77.1706},
    ]
    
    timestamps = pd.date_range("2026-10-25 00:00:00", periods=24, freq="1h", tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    
    aq_rows = []
    for ts in timestamps:
        for st in stations:
            aq_rows.append({
                "station_id": st["station_id"],
                "station_name": st["station_name"],
                "latitude": st["latitude"],
                "longitude": st["longitude"],
                "timestamp": ts,
                "pm25": round(float(np.clip(np.random.normal(160, 40), 20, 450)), 1),
                "pm10": round(float(np.clip(np.random.normal(260, 60), 40, 700)), 1),
                "no2": round(float(np.clip(np.random.normal(48, 15), 5, 150)), 1),
                "so2": round(float(np.clip(np.random.normal(14, 5), 2, 50)), 1),
                "co": round(float(np.clip(np.random.normal(1.8, 0.6), 0.2, 8.0)), 2),
                "o3": round(float(np.clip(np.random.normal(32, 12), 2, 120)), 1)
            })
    pd.DataFrame(aq_rows).to_csv(datasets_dir / "01_ground_air_quality.csv", index=False)

    # 2. Surface Meteorology (02_surface_meteorology.csv)
    met_rows = []
    for h, ts in enumerate(timestamps):
        temp_c = 18.0 + 8.0 * math.sin((h - 8) * math.pi / 12.0) + np.random.normal(0, 0.5)
        rh = 70.0 - 25.0 * math.sin((h - 8) * math.pi / 12.0) + np.random.normal(0, 2)
        dp_c = temp_c - ((100 - rh) / 5.0)
        met_rows.append({
            "timestamp": ts,
            "latitude": settings.DELHI_CENTER_LAT,
            "longitude": settings.DELHI_CENTER_LON,
            "temperature_c": round(temp_c, 1),
            "dew_point_c": round(dp_c, 1),
            "rh_pct": round(float(np.clip(rh, 10, 99)), 1),
            "wind_speed_ms": round(float(np.clip(np.random.normal(2.5, 0.8), 0.2, 10.0)), 2),
            "wind_direction_deg": round(float(np.clip(np.random.normal(315, 20), 0, 360)) % 360, 1), # North-westerly
            "pressure_hpa": round(1012.0 + np.random.normal(0, 1.5), 1),
            "solar_radiation_wm2": round(float(max(0.0, 700.0 * math.sin((h - 6) * math.pi / 12.0))), 1) if 6 <= h <= 18 else 0.0,
            "cloud_cover_fraction": round(float(np.clip(np.random.normal(0.2, 0.1), 0.0, 1.0)), 2),
            "precipitation_mm": 0.0,
            "pbl_height_m": round(float(np.clip(250 + 900 * max(0.0, math.sin((h - 7) * math.pi / 12.0)), 150, 1800)), 0)
        })
    pd.DataFrame(met_rows).to_csv(datasets_dir / "02_surface_meteorology.csv", index=False)

    # 3. Vertical Atmosphere (03_vertical_atmosphere.csv)
    vert_rows = []
    levels = settings.PRESSURE_LEVELS_HPA
    for ts in timestamps[:6]: # 6 soundings
        for p in levels:
            # Create a nighttime surface temperature inversion at 1000-950 hPa
            t_base = 18.0
            if p == 1000:
                t_p = t_base
            elif p == 950:
                t_p = t_base + 3.5 # Inversion
            elif p == 925:
                t_p = t_base + 2.0
            elif p == 900:
                t_p = t_base - 1.0
            elif p == 850:
                t_p = t_base - 5.0
            elif p == 700:
                t_p = t_base - 16.0
            else:
                t_p = t_base - 30.0

            vert_rows.append({
                "timestamp": ts,
                "pressure_level_hpa": p,
                "temperature_c": round(t_p, 1),
                "temperature_k": round(t_p + 273.15, 2),
                "wind_speed_ms": round(float(2.0 + (1000 - p) * 0.02), 2),
                "wind_direction_deg": 315.0,
                "rh_pct": 65.0,
                "pbl_height_m": 350.0
            })
    pd.DataFrame(vert_rows).to_csv(datasets_dir / "03_vertical_atmosphere.csv", index=False)

    # 6. Fire Hotspots (06_fire_hotspots.csv) - Stubble burning in Punjab/Haryana
    fire_rows = []
    lats = np.linspace(30.0, 31.8, 30) # Punjab/Haryana
    lons = np.linspace(74.5, 76.5, 30)
    for i in range(30):
        fire_rows.append({
            "fire_id": f"FIRE_2026_{i:03d}",
            "latitude": round(float(lats[i] + np.random.normal(0, 0.1)), 4),
            "longitude": round(float(lons[i] + np.random.normal(0, 0.1)), 4),
            "acq_date": "2026-10-25",
            "acq_time": "1330",
            "timestamp": "2026-10-25T13:30:00Z",
            "frp": round(float(np.random.uniform(25.0, 180.0)), 1),
            "confidence": round(float(np.random.uniform(75.0, 99.0)), 1),
            "satellite": "Suomi-NPP",
            "instrument": "VIIRS"
        })
    pd.DataFrame(fire_rows).to_csv(datasets_dir / "06_fire_hotspots.csv", index=False)

    # 7. Fire Emission Estimates (07_fire_emission_estimates.csv)
    pd.DataFrame(fire_rows).to_csv(datasets_dir / "07_fire_emission_estimates.csv", index=False)

    # 8. Satellite AOD (08_satellite_aod.csv)
    aod_rows = []
    for ts in timestamps[:12]:
        aod_rows.append({
            "timestamp": ts,
            "latitude": settings.DELHI_CENTER_LAT,
            "longitude": settings.DELHI_CENTER_LON,
            "aod_550nm": round(float(np.random.uniform(0.65, 1.45)), 3),
            "cams_pm25": 145.0,
            "cams_o3": 28.0,
            "cams_no2": 42.0,
            "cams_co": 1.6
        })
    pd.DataFrame(aod_rows).to_csv(datasets_dir / "08_satellite_aod.csv", index=False)

    # 9. Emission Inventory (09_emission_inventory.csv)
    emiss_rows = [
        {"sector": "road_transport", "anthro_nox": 28.5, "anthro_so2": 1.2, "anthro_co": 65.0, "anthro_nh3": 0.8, "anthro_voc": 32.0, "anthro_bc": 3.4, "anthro_oc": 4.1},
        {"sector": "industry", "anthro_nox": 18.2, "anthro_so2": 14.5, "anthro_co": 22.0, "anthro_nh3": 0.5, "anthro_voc": 12.0, "anthro_bc": 2.1, "anthro_oc": 3.0},
        {"sector": "power_plants", "anthro_nox": 35.0, "anthro_so2": 42.0, "anthro_co": 8.0, "anthro_nh3": 0.1, "anthro_voc": 2.0, "anthro_bc": 1.1, "anthro_oc": 0.8},
        {"sector": "residential", "anthro_nox": 5.0, "anthro_so2": 2.0, "anthro_co": 45.0, "anthro_nh3": 1.2, "anthro_voc": 24.0, "anthro_bc": 4.5, "anthro_oc": 8.2},
    ]
    pd.DataFrame(emiss_rows).to_csv(datasets_dir / "09_emission_inventory.csv", index=False)

    logger.info(f"Generated synthetic demonstration dataset pack in {datasets_dir}")


def setup_demo_cache():
    """Copy and link demonstration CSV files into data/raw directories"""
    generate_demo_datasets()
    
    src_dir = settings.DATASETS_SAMPLE_DIR
    mapping = {
        "01_ground_air_quality.csv": settings.DATA_RAW_DIR / "openaq" / "openaq_demo_2026.csv",
        "02_surface_meteorology.csv": settings.DATA_RAW_DIR / "era5" / "era5_surface_demo_2026.csv",
        "03_vertical_atmosphere.csv": settings.DATA_RAW_DIR / "era5" / "era5_vertical_demo_2026.csv",
        "06_fire_hotspots.csv": settings.DATA_RAW_DIR / "firms" / "firms_demo_2026.csv",
        "07_fire_emission_estimates.csv": settings.DATA_RAW_DIR / "gfas" / "gfas_demo_2026.csv",
        "08_satellite_aod.csv": settings.DATA_RAW_DIR / "cams" / "cams_demo_2026.csv",
        "09_emission_inventory.csv": settings.DATA_RAW_DIR / "emissions" / "emissions_demo_2026.csv"
    }

    copied = 0
    for src_file, dst_path in mapping.items():
        src_path = src_dir / src_file
        if src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            pd.read_csv(src_path).to_csv(dst_path, index=False)
            copied += 1
            logger.info(f"Loaded demo dataset: {src_file} -> {dst_path.name}")

    logger.info(f"Demo environment initialized successfully with {copied} raw datasets.")
    return True


if __name__ == "__main__":
    setup_demo_cache()
