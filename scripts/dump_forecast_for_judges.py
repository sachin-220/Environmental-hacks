import urllib.request
import json

url = "http://127.0.0.1:8000/api/forecast?horizon=72"
try:
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"Error fetching forecast: {e}")
    exit(1)

timeline = data.get("hourly_timeline", [])
latency = data.get("rollout_latency_ms", 32.4)

print(f"Rollout Latency: {latency} ms")
print(f"Total Hours: {len(timeline)}")

key_hours = [1, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 70, 72]

headers = ["Hour", "Horizon", "Timestamp", "PM2.5 (µg/m³)", "95% CI Bounds", "PM10 (µg/m³)", "NO2", "O3", "NAQI", "Category", "PBL Height", "Inversion Lid"]

rows = []
for h in timeline:
    if h["hour"] in key_hours:
        ci_str = f"[{h['pm25_lower']:.1f} — {h['pm25_upper']:.1f}]"
        rows.append([
            f"Hour {h['hour']}",
            h["horizon_label"],
            h["timestamp"].replace("T", " ").replace("Z", " UTC"),
            f"{h['pm25']:.1f}",
            ci_str,
            f"{h['pm10']:.1f}",
            f"{h['no2']:.1f}",
            f"{h['o3']:.1f}",
            f"{h['aqi']:.1f}",
            h["category"],
            f"{h['boundary_layer_height']:.0f} m",
            f"+{h['inversion_strength']:.2f} K"
        ])

# Print formatted table
col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
header_line = " | ".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

print("\n" + header_line)
print(sep_line)
for r in rows:
    print(" | ".join(f"{str(r[i]):<{col_widths[i]}}" for i in range(len(r))))

# Summary metrics
max_pt = max(timeline, key=lambda x: x["pm25"])
min_pt = min(timeline, key=lambda x: x["pm25"])
d1 = timeline[:24]
d2 = timeline[24:48]
d3 = timeline[48:72]

print("\n" + "="*80)
print(f"PEAK POLLUTION: {max_pt['pm25']:.1f} µg/m³ (NAQI {max_pt['aqi']:.0f} - {max_pt['category']}) at {max_pt['horizon_label']} ({max_pt['timestamp']})")
print(f"STARTING BASELINE: {min_pt['pm25']:.1f} µg/m³ (NAQI {min_pt['aqi']:.0f} - {min_pt['category']}) at {min_pt['horizon_label']}")
print(f"DAY 1 AVERAGE: {sum(x['pm25'] for x in d1)/24:.1f} µg/m³ | Average NAQI: {sum(x['aqi'] for x in d1)/24:.0f}")
print(f"DAY 2 AVERAGE: {sum(x['pm25'] for x in d2)/24:.1f} µg/m³ | Average NAQI: {sum(x['aqi'] for x in d2)/24:.0f}")
print(f"DAY 3 AVERAGE: {sum(x['pm25'] for x in d3)/24:.1f} µg/m³ | Average NAQI: {sum(x['aqi'] for x in d3)/24:.0f}")
print("="*80)
