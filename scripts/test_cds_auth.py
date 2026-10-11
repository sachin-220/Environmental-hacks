import urllib.request
import urllib.error
import json

CDS_KEY = "fd4d08d9-f3cd-4648-ae82-6e2669829f2f"

endpoints = [
    ("User Info", "https://cds.climate.copernicus.eu/api/catalogue/v1/user"),
    ("Retrieve Jobs", "https://cds.climate.copernicus.eu/api/retrieve/v1/jobs"),
    ("Retrieve Processes", "https://cds.climate.copernicus.eu/api/retrieve/v1/processes"),
    ("Old CDS API", "https://cds.climate.copernicus.eu/api/v2")
]

for label, url in endpoints:
    print(f"\n--- Testing {label}: {url} ---")
    
    # 1. With PRIVATE-TOKEN header (new CDS standard)
    req1 = urllib.request.Request(url, headers={
        "PRIVATE-TOKEN": CDS_KEY,
        "User-Agent": "SAMEER-AERIS/1.0"
    })
    try:
        with urllib.request.urlopen(req1, timeout=10) as resp:
            print(f"PRIVATE-TOKEN -> Status: {resp.status}, Body: {resp.read().decode('utf-8')[:200]}")
    except urllib.error.HTTPError as e:
        print(f"PRIVATE-TOKEN -> HTTP Error {e.code}: {e.read().decode('utf-8')[:200]}")
    except Exception as e:
        print(f"PRIVATE-TOKEN -> Error: {e}")

    # 2. With Bearer token header
    req2 = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {CDS_KEY}",
        "User-Agent": "SAMEER-AERIS/1.0"
    })
    try:
        with urllib.request.urlopen(req2, timeout=10) as resp:
            print(f"Authorization: Bearer -> Status: {resp.status}, Body: {resp.read().decode('utf-8')[:200]}")
    except urllib.error.HTTPError as e:
        print(f"Authorization: Bearer -> HTTP Error {e.code}: {e.read().decode('utf-8')[:200]}")
    except Exception as e:
        print(f"Authorization: Bearer -> Error: {e}")
