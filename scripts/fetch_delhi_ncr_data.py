"""
Delhi NCR Data Ingestion & Extraction Script
Fetches and saves live air quality station data and satellite data specifically for Delhi NCR.
"""
import sys
from pathlib import Path
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import settings

# Delhi NCR Coordinates (D03 Inner Domain)
DELHI_NCR_BOUNDS = {
    "west": 76.80,
    "south": 28.20,
    "east": 77.60,
    "north": 28.90
}

def fetch_delhi_openaq():
    print(f"[*] Fetching live OpenAQ ground air quality stations within Delhi NCR ({DELHI_NCR_BOUNDS})...")
    bbox_str = f"{DELHI_NCR_BOUNDS['west']},{DELHI_NCR_BOUNDS['south']},{DELHI_NCR_BOUNDS['east']},{DELHI_NCR_BOUNDS['north']}"
    url = f"https://api.openaq.org/v3/locations?bbox={bbox_str}&limit=50"
    headers = {"X-API-Key": settings.OPENAQ_API_KEY}
    
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        print(f"[-] OpenAQ Error: HTTP {resp.status_code}")
        return pd.DataFrame()
    
    locations = resp.json().get("results", [])
    print(f"[+] Found {len(locations)} monitoring stations in Delhi NCR.")
    
    records = []
    for loc in locations:
        loc_id = loc.get("id")
        loc_name = loc.get("name")
        coords = loc.get("coordinates", {})
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        
        # Query sensors
        s_url = f"https://api.openaq.org/v3/locations/{loc_id}/sensors"
        try:
            s_resp = requests.get(s_url, headers=headers, timeout=10)
            if s_resp.status_code == 200:
                for sensor in s_resp.json().get("results", []):
                    param_info = sensor.get("parameter", {})
                    p_name = param_info.get("name")
                    p_units = param_info.get("units")
                    latest = sensor.get("latest", {}) or {}
                    val = latest.get("value")
                    dt = latest.get("datetime")
                    
                    records.append({
                        "station_id": loc_id,
                        "station_name": loc_name,
                        "latitude": lat,
                        "longitude": lon,
                        "pollutant": p_name,
                        "value": val,
                        "unit": p_units,
                        "datetime_utc": dt
                    })
        except Exception as e:
            pass
            
    df = pd.DataFrame(records)
    return df


def fetch_delhi_firms():
    print(f"[*] Fetching live NASA FIRMS active fire hotspots within Delhi NCR...")
    area_str = f"{DELHI_NCR_BOUNDS['west']},{DELHI_NCR_BOUNDS['south']},{DELHI_NCR_BOUNDS['east']},{DELHI_NCR_BOUNDS['north']}"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{settings.FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/{area_str}/1"
    
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            lines = [line for line in resp.text.strip().split("\n") if line]
            if len(lines) > 1:
                import io
                df = pd.read_csv(io.StringIO(resp.text))
                print(f"[+] Found {len(df)} active thermal anomalies in Delhi NCR.")
                return df
            else:
                print("[+] NASA FIRMS reports 0 active fire hotspots inside Delhi NCR borders (Clean / Urban zone).")
                return pd.DataFrame()
        else:
            print(f"[-] FIRMS returned HTTP {resp.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"[-] FIRMS error: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    df_aq = fetch_delhi_openaq()
    out_dir = settings.DATA_RAW_DIR / "delhi_ncr"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not df_aq.empty:
        csv_path = out_dir / "delhi_ncr_live_air_quality.csv"
        df_aq.to_csv(csv_path, index=False)
        print(f"[+] Successfully saved Delhi NCR air quality data to: {csv_path}")
        print("\nSummary of Pollutants Monitored in Delhi NCR:")
        print(df_aq.groupby("pollutant")["value"].describe())
        
    df_firms = fetch_delhi_firms()
    if not df_firms.empty:
        firms_path = out_dir / "delhi_ncr_live_fires.csv"
        df_firms.to_csv(firms_path, index=False)
        print(f"[+] Saved Delhi NCR fire data to: {firms_path}")
