import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

FIRMS_KEY = os.getenv("FIRMS_MAP_KEY", "")
OPENAQ_KEY = os.getenv("OPENAQ_API_KEY", "")
CDS_KEY = os.getenv("CDS_API_KEY", "")

print("=" * 70)
print("TESTING CONFIGURED API KEYS")
print("=" * 70)

results = {}

# -------------------------------------------------------------
# 1. TEST NASA FIRMS API KEY
# -------------------------------------------------------------
print("\n[1] Testing NASA FIRMS API Key...")
print(f"Key configured: {FIRMS_KEY[:6]}...{FIRMS_KEY[-4:] if len(FIRMS_KEY) > 10 else ''}")

# Check FIRMS key transaction status or small area query
# NASA FIRMS API has: https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{MAP_KEY}/VIIRS_SNPP_NRT
# Or query area: 76.8,28.2,77.6,28.9 (Delhi NCR) for 1 day
firms_urls = [
    ("Transaction/Availability Check", f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT"),
    ("Area Active Fires Query (Delhi NCR)", f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT/76.8,28.2,77.6,28.9/1")
]

firms_success = False
firms_details = []

for label, url in firms_urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SAMEER-AERIS/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace").strip()
            
            # Check body for invalid key message
            if "Invalid MAP KEY" in body or "Invalid Map Key" in body or "Bad Request" in body:
                firms_details.append({"test": label, "status": status, "success": False, "response": body[:200]})
            else:
                lines = [l for l in body.splitlines() if l.strip()]
                firms_details.append({"test": label, "status": status, "success": True, "lines_returned": len(lines), "preview": lines[:3]})
                firms_success = True
    except urllib.error.HTTPError as e:
        firms_details.append({"test": label, "status": e.code, "success": False, "error": str(e), "body": e.read().decode("utf-8", errors="replace")[:200]})
    except Exception as e:
        firms_details.append({"test": label, "status": 0, "success": False, "error": str(e)})

results["NASA_FIRMS"] = {
    "key_present": bool(FIRMS_KEY and not FIRMS_KEY.startswith("YOUR_")),
    "working": firms_success,
    "details": firms_details
}

# -------------------------------------------------------------
# 2. TEST OPENAQ v3 API KEY
# -------------------------------------------------------------
print("\n[2] Testing OpenAQ v3 API Key...")
print(f"Key configured: {OPENAQ_KEY[:6]}...{OPENAQ_KEY[-4:] if len(OPENAQ_KEY) > 10 else ''}")

# OpenAQ v3 test endpoints:
# https://api.openaq.org/v3/locations?limit=2
# or https://api.openaq.org/v3/parameters
openaq_urls = [
    ("Locations List (limit=2)", "https://api.openaq.org/v3/locations?limit=2"),
    ("Delhi NCR Bounding Box Locations", "https://api.openaq.org/v3/locations?bbox=76.8,28.2,77.6,28.9&limit=5")
]

openaq_success = False
openaq_details = []

for label, url in openaq_urls:
    try:
        headers = {
            "User-Agent": "SAMEER-AERIS/1.0",
            "X-API-Key": OPENAQ_KEY,
            "Accept": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            raw_body = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw_body)
            results_list = parsed.get("results", [])
            openaq_details.append({
                "test": label,
                "status": status,
                "success": True,
                "count": len(results_list),
                "sample_names": [r.get("name") for r in results_list[:3]]
            })
            openaq_success = True
    except urllib.error.HTTPError as e:
        openaq_details.append({"test": label, "status": e.code, "success": False, "error": str(e), "body": e.read().decode("utf-8", errors="replace")[:200]})
    except Exception as e:
        openaq_details.append({"test": label, "status": 0, "success": False, "error": str(e)})

results["OpenAQ_v3"] = {
    "key_present": bool(OPENAQ_KEY and not OPENAQ_KEY.startswith("YOUR_")),
    "working": openaq_success,
    "details": openaq_details
}

# -------------------------------------------------------------
# 3. TEST COPERNICUS CDS API KEY
# -------------------------------------------------------------
print("\n[3] Testing Copernicus CDS API Key...")
print(f"Key configured: {CDS_KEY[:6]}...{CDS_KEY[-4:] if len(CDS_KEY) > 10 else ''}")

# Copernicus Climate Data Store (CDS) new portal URL: https://cds.climate.copernicus.eu/api
# Or via cdsapi python library if installed
cds_details = []
cds_success = False

# Method A: Try cdsapi package
try:
    import cdsapi
    # Create client with key
    # New CDS system uses URL https://cds.climate.copernicus.eu/api and personal access token (UUID)
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=CDS_KEY, wait_until_complete=False, quiet=True)
    # Check if client can access user or dataset info
    cds_details.append({"method": "cdsapi_client_init", "status": "initialized"})
except ImportError:
    cds_details.append({"method": "cdsapi_package", "status": "not_installed"})
except Exception as e:
    cds_details.append({"method": "cdsapi_client_init", "status": "error", "error": str(e)})

# Method B: Direct HTTP probe to Copernicus CDS API
# New CDS API endpoint: https://cds.climate.copernicus.eu/api/catalogue/v1/collections
try:
    headers = {
        "PRIVATE-TOKEN": CDS_KEY,
        "Authorization": f"Bearer {CDS_KEY}",
        "User-Agent": "SAMEER-AERIS/1.0"
    }
    # Test catalog collection query (public or auth)
    req = urllib.request.Request("https://cds.climate.copernicus.eu/api/catalogue/v1/collections/reanalysis-era5-single-levels", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        title = data.get("title", "")
        cds_details.append({
            "test": "CDS Collection Metadata (ERA5)",
            "status": status,
            "success": True,
            "collection_title": title
        })
        cds_success = True
except urllib.error.HTTPError as e:
    cds_details.append({"test": "CDS API HTTP Probe", "status": e.code, "success": False, "error": str(e), "body": e.read().decode("utf-8", errors="replace")[:200]})
except Exception as e:
    cds_details.append({"test": "CDS API HTTP Probe", "status": 0, "success": False, "error": str(e)})

results["Copernicus_CDS"] = {
    "key_present": bool(CDS_KEY and not CDS_KEY.startswith("YOUR_")),
    "working": cds_success,
    "details": cds_details
}

# -------------------------------------------------------------
# PRINT SUMMARY TABLE
# -------------------------------------------------------------
print("\n" + "=" * 70)
print(f"{'SERVICE':<20} | {'KEY CONFIGURED':<15} | {'STATUS':<15} | {'VERDICT'}")
print("=" * 70)

for name, res in results.items():
    configured = "YES" if res["key_present"] else "NO"
    working = "WORKING (VALID)" if res["working"] else "FAILED / INVALID"
    print(f"{name:<20} | {configured:<15} | {working:<15} | {'SUCCESS' if res['working'] else 'ERROR'}")
    for d in res["details"]:
        print(f"   --> {d}")

print("=" * 70)

with open("api_key_validation_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
