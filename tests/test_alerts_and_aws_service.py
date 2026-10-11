"""
Integration and regression tests for AERIS Hyper-Local Citizen Geo-Alerts,
School Safety Action Protocol, and AWS Free Tier Infrastructure Services.
"""
import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_get_monitored_wards():
    """Verifies that all Delhi NCR geographic wards are returned with sensitivities and baselines"""
    res = client.get("/api/alerts/wards")
    assert res.status_code == 200
    data = res.json()
    assert "wards" in data
    assert len(data["wards"]) >= 8
    
    # Check Anand Vihar and Bawana / DTU presence
    ward_ids = [w["id"] for w in data["wards"]]
    assert "anand_vihar" in ward_ids
    assert "bawana_dtu" in ward_ids
    assert "rohini" in ward_ids


def test_get_active_geo_alerts():
    """Verifies that hyper-local active alerts and health advisories are computed across wards"""
    res = client.get("/api/alerts/active")
    assert res.status_code == 200
    data = res.json()
    assert data["active_alerts_count"] >= 1
    assert "alerts" in data
    
    first_alert = data["alerts"][0]
    assert "current_aqi" in first_alert
    assert "health_advisory" in first_alert
    assert "vulnerable_groups" in first_alert["health_advisory"]
    assert "outdoor_jogging" in first_alert["health_advisory"]
    assert "school_protocol" in first_alert


def test_dispatch_alert_broadcast():
    """Verifies that emergency multi-channel alert dispatch succeeds and logs to audit history"""
    payload = {
        "ward_id": "anand_vihar",
        "severity": "SEVERE",
        "category": "NOCTURNAL_INVERSION_COLLAPSE",
        "title": "Severe Smog Inversion Warning",
        "message": "Boundary layer dropping below 210m. Suspend outdoor evening activities.",
        "target_audiences": ["schools", "citizens"],
        "channels": ["web_push", "whatsapp", "sms"]
    }
    res = client.post("/api/alerts/broadcast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "alert_id" in data
    assert data["recipients_reached"] > 0
    assert "web_push_payload" in data


def test_citizen_subscription():
    """Verifies citizen / school enrollment into the notification database"""
    payload = {
        "name": "Prof. S. Sharma (DTU Coordinator)",
        "phone": "+91 9811122233",
        "email": "sharma@dtu.ac.in",
        "ward_id": "bawana_dtu",
        "role": "school_admin",
        "channels": ["push", "whatsapp"]
    }
    res = client.post("/api/alerts/subscribe", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "subscription_id" in data
    assert "Bawana / DTU" in data["ward"]


def test_school_safety_protocol():
    """Verifies structured CPCB / AERIS 5-tier school safety action protocol"""
    res = client.get("/api/alerts/schools")
    assert res.status_code == 200
    data = res.json()
    assert "school_guidelines" in data
    assert len(data["school_guidelines"]) == 5
    assert data["total_schools_covered_ncr"] >= 2000


def test_aws_infrastructure_health():
    """Verifies live telemetry reporting for all 8 AWS Free Tier services"""
    res = client.get("/api/aws/health")
    assert res.status_code == 200
    data = res.json()
    assert data["compliance_mode"] == "100% AWS FREE TIER COMPLIANT (Zero Infrastructure Cost for Municipalities)"
    assert len(data["services"]) == 8
    
    svc_names = [s["name"] for s in data["services"]]
    assert any("CloudFront" in name for name in svc_names)
    assert any("S3" in name for name in svc_names)
    assert any("EC2" in name for name in svc_names)
    assert any("Lambda" in name for name in svc_names)
    assert any("EventBridge" in name for name in svc_names)
    assert any("DynamoDB" in name for name in svc_names)
    assert any("SNS" in name for name in svc_names)
    assert any("CloudWatch" in name for name in svc_names)
