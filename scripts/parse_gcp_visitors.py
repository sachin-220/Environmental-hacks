import subprocess
import json
from collections import defaultdict
from datetime import datetime

print("Fetching Cloud Run request logs from Google Cloud...")

cmd = [
    "gcloud.cmd", "logging", "read",
    "resource.type=cloud_run_revision AND logName:run.googleapis.com%2Frequests",
    "--project=chain-of-title-cinema-2026",
    "--limit=1000",
    "--format=json"
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    logs = json.loads(res.stdout)
except Exception as e:
    print(f"Error fetching logs: {e}")
    logs = []

print(f"Total request log entries retrieved: {len(logs)}")

# Analyze unique visitors by remoteIp
visitors = defaultdict(lambda: {
    "ip": "",
    "user_agents": set(),
    "first_seen": None,
    "last_seen": None,
    "total_requests": 0,
    "urls_visited": set(),
    "status_codes": set(),
    "referers": set(),
    "trace_ids": []
})

for entry in logs:
    http = entry.get("httpRequest", {})
    ip = http.get("remoteIp", "Unknown")
    ts = entry.get("timestamp")
    ua = http.get("userAgent", "Unknown")
    url = http.get("requestUrl", "")
    status = http.get("status", 0)
    ref = http.get("referer", "")
    trace = entry.get("trace", "")
    if trace:
        trace_id = trace.split("/")[-1]
    else:
        trace_id = entry.get("insertId", "")
        
    v = visitors[ip]
    v["ip"] = ip
    v["user_agents"].add(ua)
    v["total_requests"] += 1
    v["urls_visited"].add(url)
    v["status_codes"].add(status)
    if ref:
        v["referers"].add(ref)
    if trace_id and trace_id not in v["trace_ids"]:
        v["trace_ids"].append(trace_id)
        
    if ts:
        if v["first_seen"] is None or ts < v["first_seen"]:
            v["first_seen"] = ts
        if v["last_seen"] is None or ts > v["last_seen"]:
            v["last_seen"] = ts

output = {
    "total_unique_visitors": len(visitors),
    "visitors": []
}

for ip, v in sorted(visitors.items(), key=lambda x: x[1]["total_requests"], reverse=True):
    output["visitors"].append({
        "remote_ip": ip,
        "total_requests": v["total_requests"],
        "first_seen": v["first_seen"],
        "last_seen": v["last_seen"],
        "user_agents": list(v["user_agents"]),
        "urls_visited": list(v["urls_visited"]),
        "status_codes": list(v["status_codes"]),
        "referers": list(v["referers"]),
        "sample_trace_or_visitor_id": v["trace_ids"][:5]
    })

with open("gcp_visitors_report.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 80)
print(f"TOTAL UNIQUE VISITORS IDENTIFIED: {len(visitors)}")
print("=" * 80)
for i, v in enumerate(output["visitors"], 1):
    print(f"\n[Visitor #{i}]")
    print(f"IP Address: {v['remote_ip']}")
    print(f"Total Requests: {v['total_requests']}")
    print(f"First Seen: {v['first_seen']}")
    print(f"Last Seen:  {v['last_seen']}")
    print(f"User Agent: {v['user_agents'][0] if v['user_agents'] else 'Unknown'}")
    print(f"URLs Visited: {v['urls_visited']}")
    print(f"Status Codes: {v['status_codes']}")
    print(f"Request/Trace IDs: {v['sample_trace_or_visitor_id']}")

