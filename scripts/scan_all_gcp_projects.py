import subprocess
import json

projects = [
    "chain-of-title-cinema-2026",
    "cedar-helper-448019-i2",
    "emailbotproject-465211",
    "gen-lang-client-0277364523",
    "gen-lang-client-0389020603",
    "gen-lang-client-0648955987",
    "inspired-truth-454518-u6",
    "nc-stall",
    "project-75499b23-323a-4c34-aa3"
]

all_visitors = {}

for proj in projects:
    print(f"Checking project: {proj}...")
    cmd = [
        "gcloud.cmd", "logging", "read",
        "httpRequest:*",
        f"--project={proj}",
        "--limit=500",
        "--format=json"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            logs = json.loads(res.stdout)
            print(f"  -> Found {len(logs)} HTTP request entries in {proj}!")
            for entry in logs:
                http = entry.get("httpRequest", {})
                ip = http.get("remoteIp", "Unknown")
                ts = entry.get("timestamp")
                ua = http.get("userAgent", "Unknown")
                url = http.get("requestUrl", "")
                status = http.get("status", 0)
                trace = entry.get("trace", "")
                insert_id = entry.get("insertId", "")
                trace_id = trace.split("/")[-1] if trace else insert_id
                
                key = (proj, ip)
                if key not in all_visitors:
                    all_visitors[key] = {
                        "project": proj,
                        "ip": ip,
                        "user_agents": set(),
                        "first_seen": ts,
                        "last_seen": ts,
                        "total_requests": 0,
                        "urls_visited": set(),
                        "status_codes": set(),
                        "trace_ids": []
                    }
                v = all_visitors[key]
                v["total_requests"] += 1
                v["user_agents"].add(ua)
                v["urls_visited"].add(url)
                v["status_codes"].add(status)
                if ts:
                    if not v["first_seen"] or ts < v["first_seen"]:
                        v["first_seen"] = ts
                    if not v["last_seen"] or ts > v["last_seen"]:
                        v["last_seen"] = ts
                if trace_id and trace_id not in v["trace_ids"]:
                    v["trace_ids"].append(trace_id)
        else:
            err = res.stderr.strip()
            if "API [logging.googleapis.com] not enabled" in err:
                print(f"  -> Logging API disabled in {proj}")
            elif "PERMISSION_DENIED" in err:
                print(f"  -> Permission denied in {proj}")
            else:
                print(f"  -> No HTTP logs in {proj}")
    except Exception as e:
        print(f"  -> Error: {e}")

print("\n" + "=" * 80)
print(f"TOTAL UNIQUE VISITORS FOUND ACROSS ALL PROJECTS: {len(all_visitors)}")
print("=" * 80)

for (proj, ip), v in all_visitors.items():
    print(f"\nProject: {proj}")
    print(f"Visitor Remote IP: {ip}")
    print(f"Total Requests: {v['total_requests']}")
    print(f"First Seen: {v['first_seen']}")
    print(f"Last Seen:  {v['last_seen']}")
    print(f"User Agent: {list(v['user_agents'])}")
    print(f"URLs Visited: {list(v['urls_visited'])}")
    print(f"Request Trace IDs: {v['trace_ids']}")

