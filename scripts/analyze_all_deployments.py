import subprocess
import json
from collections import defaultdict
from datetime import datetime

print("Querying Google Cloud Logging for ALL revisions since 2026-09-01...")

# Query with timestamp >= "2026-09-01T00:00:00Z"
cmd = [
    "gcloud.cmd", "logging", "read",
    'resource.type="cloud_run_revision" AND logName:"run.googleapis.com%2Frequests" AND timestamp>="2026-09-01T00:00:00Z"',
    "--project=chain-of-title-cinema-2026",
    "--limit=5000",
    "--format=json"
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    logs = json.loads(res.stdout)
except Exception as e:
    print(f"Error fetching logs: {e}")
    logs = []

print(f"Total requests retrieved across all revisions: {len(logs)}")

# Data structures for tracking
visitors = defaultdict(lambda: {
    "ip": "",
    "user_agents": set(),
    "first_seen": None,
    "last_seen": None,
    "total_requests": 0,
    "revisions_visited": set(),
    "urls_visited": set(),
    "status_codes": set(),
    "trace_ids": []
})

revisions_summary = defaultdict(lambda: {
    "total_requests": 0,
    "unique_ips": set(),
    "urls": set()
})

for entry in logs:
    http = entry.get("httpRequest", {})
    ip = http.get("remoteIp", "Unknown")
    ts = entry.get("timestamp")
    ua = http.get("userAgent", "Unknown")
    url = http.get("requestUrl", "")
    status = http.get("status", 0)
    trace = entry.get("trace", "")
    trace_id = trace.split("/")[-1] if trace else entry.get("insertId", "")
    
    resource = entry.get("resource", {}).get("labels", {})
    rev = resource.get("revision_name", "unknown_revision")
    
    # Update revision summary
    revisions_summary[rev]["total_requests"] += 1
    revisions_summary[rev]["unique_ips"].add(ip)
    revisions_summary[rev]["urls"].add(url)
    
    # Update visitor summary
    v = visitors[ip]
    v["ip"] = ip
    v["user_agents"].add(ua)
    v["total_requests"] += 1
    v["revisions_visited"].add(rev)
    v["urls_visited"].add(url)
    v["status_codes"].add(status)
    if trace_id and trace_id not in v["trace_ids"]:
        v["trace_ids"].append(trace_id)
        
    if ts:
        if v["first_seen"] is None or ts < v["first_seen"]:
            v["first_seen"] = ts
        if v["last_seen"] is None or ts > v["last_seen"]:
            v["last_seen"] = ts

output = {
    "total_requests_all_time": len(logs),
    "total_unique_visitors": len(visitors),
    "revisions": {k: {"total_requests": v["total_requests"], "unique_visitors_count": len(v["unique_ips"]), "unique_ips": list(v["unique_ips"])} for k, v in revisions_summary.items()},
    "visitors": []
}

for ip, v in sorted(visitors.items(), key=lambda x: x[1]["total_requests"], reverse=True):
    output["visitors"].append({
        "remote_ip": ip,
        "total_requests": v["total_requests"],
        "first_seen": v["first_seen"],
        "last_seen": v["last_seen"],
        "revisions_visited": sorted(list(v["revisions_visited"])),
        "user_agents": list(v["user_agents"]),
        "urls_visited": sorted(list(v["urls_visited"])),
        "status_codes": sorted(list(v["status_codes"])),
        "sample_trace_ids": v["trace_ids"][:5]
    })

with open("all_deployments_visitors_report.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 80)
print(f"TOTAL LOG ENTRIES: {len(logs)}")
print(f"TOTAL UNIQUE VISITORS ACROSS ALL DEPLOYMENTS: {len(visitors)}")
print("=" * 80)

print("\n--- REVISIONS BREAKDOWN ---")
for rev, r_data in sorted(output["revisions"].items()):
    print(f"Revision {rev}: {r_data['total_requests']} requests, {r_data['unique_visitors_count']} unique visitor(s) {r_data['unique_ips']}")

print("\n--- UNIQUE VISITORS DETAILS ---")
for i, v in enumerate(output["visitors"], 1):
    print(f"\n[Visitor #{i}]")
    print(f"IP: {v['remote_ip']}")
    print(f"Total Requests: {v['total_requests']}")
    print(f"First Seen: {v['first_seen']}")
    print(f"Last Seen:  {v['last_seen']}")
    print(f"Revisions Visited: {v['revisions_visited']}")
    print(f"User Agents: {v['user_agents']}")
    print(f"URLs Visited: {v['urls_visited']}")
    print(f"Trace IDs: {v['sample_trace_ids']}")
