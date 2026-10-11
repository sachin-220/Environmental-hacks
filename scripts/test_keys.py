"""
Test script to validate external API keys configured in SAMEER:
1. NASA FIRMS MAP Key
2. OpenAQ v3 API Key
3. Copernicus CDS API Key
"""
import os
import sys
from pathlib import Path
import requests

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def test_firms_key():
    print("=" * 60)
    print("1. NASA FIRMS (Fire Information for Resource Management System)")
    print("=" * 60)
    key = settings.FIRMS_MAP_KEY
    if not key:
        print("[-] FIRMS_MAP_KEY is not configured.")
        return False, "Not configured"

    masked = f"{key[:6]}...{key[-4:]}"
    print(f"[*] Testing MAP Key: {masked} (length: {len(key)})")

    # FIRMS API check
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/73.5,27.0,78.5,32.5/1"
    try:
        resp = requests.get(url, timeout=20)
        print(f"[*] Response HTTP Status: {resp.status_code}")
        text = resp.text.strip()
        print(f"[*] Response Body Preview:\n{text[:300]}")

        if resp.status_code == 200:
            if "Invalid Map Key" in text or "error" in text.lower() or "exception" in text.lower():
                print("[-] Result: FAILED (API returned 200 with error message: Invalid Map Key)")
                return False, f"Invalid Map Key response: {text}"
            else:
                print("[+] Result: SUCCESS (Valid key, returned CSV fire data)")
                return True, "Valid and working"
        elif resp.status_code == 403 or resp.status_code == 401:
            print("[-] Result: FAILED (Unauthorized / Forbidden)")
            return False, f"HTTP {resp.status_code}"
        else:
            print(f"[-] Result: UNEXPECTED STATUS (HTTP {resp.status_code})")
            return False, f"HTTP {resp.status_code}: {text[:100]}"
    except Exception as e:
        print(f"[-] Request Error: {e}")
        return False, str(e)


def test_openaq_key():
    print("\n" + "=" * 60)
    print("2. OpenAQ API (v3)")
    print("=" * 60)
    key = settings.OPENAQ_API_KEY
    if not key:
        print("[-] OPENAQ_API_KEY is not configured.")
        return False, "Not configured"

    masked = f"{key[:6]}...{key[-4:]}"
    print(f"[*] Testing OpenAQ Key: {masked} (length: {len(key)})")

    url = "https://api.openaq.org/v3/locations"
    headers = {"X-API-Key": key}
    params = {"limit": 2}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        print(f"[*] Response HTTP Status: {resp.status_code}")
        print(f"[*] Response Body Preview:\n{resp.text[:300]}")

        if resp.status_code == 200:
            data = resp.json()
            results_count = len(data.get("results", []))
            print(f"[+] Result: SUCCESS (Valid key, returned {results_count} locations)")
            return True, f"Valid and working ({results_count} locations returned)"
        elif resp.status_code in (401, 403):
            print(f"[-] Result: FAILED (Unauthorized/Forbidden HTTP {resp.status_code})")
            return False, f"Unauthorized (HTTP {resp.status_code}): {resp.text}"
        elif resp.status_code == 429:
            print("[-] Result: RATE LIMITED (HTTP 429)")
            return False, "Rate limited (HTTP 429)"
        else:
            print(f"[-] Result: UNEXPECTED STATUS (HTTP {resp.status_code})")
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        print(f"[-] Request Error: {e}")
        return False, str(e)


def test_cds_key():
    print("\n" + "=" * 60)
    print("3. Copernicus Climate Data Store (CDS)")
    print("=" * 60)
    key = settings.CDS_API_KEY
    if not key:
        print("[-] CDS_API_KEY is not configured.")
        return False, "Not configured"

    masked = f"{key[:6]}...{key[-4:]}"
    print(f"[*] Testing CDS Key: {masked} (length: {len(key)})")

    # The new CDS system (since 2024) is at https://cds.climate.copernicus.eu/api
    # Authentication token is passed in header 'PRIVATE-TOKEN' or Authorization
    success = False
    details = []

    # 1. Test direct HTTP against new CDS API catalogue/user endpoint
    endpoints_to_try = [
        ("New CDS API (catalogue)", "https://cds.climate.copernicus.eu/api/catalogue/v1/datasets?limit=1", {"PRIVATE-TOKEN": key}),
        ("New CDS API (auth check)", "https://cds.climate.copernicus.eu/api/retrieve/v1/jobs", {"PRIVATE-TOKEN": key}),
        ("Legacy CDS API (v2)", "https://cds.climate.copernicus.eu/api/v2/resources", {"PRIVATE-TOKEN": key})
    ]

    for label, url, headers in endpoints_to_try:
        try:
            print(f"\n[*] Probing {label} at {url}...")
            resp = requests.get(url, headers=headers, timeout=20)
            print(f"    HTTP Status: {resp.status_code}")
            print(f"    Body: {resp.text[:200]}")
            if resp.status_code in (200, 201):
                success = True
                details.append(f"{label}: HTTP 200 OK")
            elif resp.status_code in (401, 403):
                details.append(f"{label}: HTTP {resp.status_code} Unauthorized/Forbidden")
            else:
                details.append(f"{label}: HTTP {resp.status_code}")
        except Exception as ex:
            print(f"    Probe Error: {ex}")
            details.append(f"{label}: Exception {ex}")

    # 2. Test via python cdsapi package if installed
    try:
        import cdsapi
        print(f"\n[*] Testing via `cdsapi` library (version {getattr(cdsapi, '__version__', 'unknown')})...")
        os.environ["CDSAPI_URL"] = "https://cds.climate.copernicus.eu/api"
        os.environ["CDSAPI_KEY"] = key
        c = cdsapi.Client(wait_until_complete=False, quiet=True)
        print(f"    cdsapi client instantiated pointing to: {c.url}")
        # Test a minimal catalogue search / check
        if hasattr(c, "get_remote"):
            # New cdsapi method
            try:
                res = c.get_remote(c.url + "/catalogue/v1/datasets?limit=1")
                print(f"    cdsapi remote check: {res}")
            except Exception as e:
                print(f"    cdsapi remote check note: {e}")
    except ImportError:
        print("    cdsapi package not installed.")
    except Exception as ex:
        print(f"    cdsapi test exception: {ex}")

    if success:
        print("[+] Result: SUCCESS (Key authenticated successfully with Copernicus CDS)")
        return True, "; ".join(details)
    else:
        print("[-] Result: FAILED or UNAUTHORIZED")
        return False, "; ".join(details)


if __name__ == "__main__":
    r_firms, m_firms = test_firms_key()
    r_openaq, m_openaq = test_openaq_key()
    r_cds, m_cds = test_cds_key()

    print("\n" + "=" * 60)
    print("FINAL SUMMARY REPORT")
    print("=" * 60)
    print(f"1. NASA FIRMS API:     {'[PASSED]' if r_firms else '[FAILED]'} -> {m_firms}")
    print(f"2. OpenAQ v3 API:       {'[PASSED]' if r_openaq else '[FAILED]'} -> {m_openaq}")
    print(f"3. Copernicus CDS API:  {'[PASSED]' if r_cds else '[FAILED]'} -> {m_cds}")
