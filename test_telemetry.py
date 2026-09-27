import sys
sys.path.insert(0, r'C:\Advi\Collegestuff\Events\SIH\zenith')
sys.path.insert(0, r'C:\Advi\Collegestuff\Events\SIH\zenith\backend')
from fastapi.testclient import TestClient
from zenith_backend.main import app

client = TestClient(app)

# Test 1: Send valid telemetry
print("=== Test 1: Send valid telemetry ===")
resp = client.post('/api/v1/telemetry', json={
    "timestamp": "2026-01-15T10:30:00Z",
    "asset_id": 1,
    "event_type": "vulnerability_discovered",
    "severity": 85,
    "vulnerability_id": "VULN-001",
    "threat_likelihood": 0.62,
    "control_effectiveness": 0.55,
    "source": "SIEM-01"
})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Telemetry ID: {data['stored_event']['telemetry_id']}")
    print(f"Asset: {data['stored_event']['asset_name']}")
    print(f"Event: {data['stored_event']['event_type']}")
    print(f"Severity: {data['stored_event']['severity']}")
    print(f"Threat likelihood: {data['stored_event']['threat_likelihood']}")
    print(f"Control effectiveness: {data['stored_event']['control_effectiveness']}")
    print(f"Source: {data['stored_event']['source']}")
    print(f"Updated risk score: {data['updated_risk_assessment']['risk_score']}")
    print(f"Risk level: {data['updated_risk_assessment']['risk_level']}")
    print(f"ALE: {data['updated_risk_assessment']['ale']}")
    print(f"Message: {data['message']}")
else:
    print(f"Error: {resp.json()}")

print()

# Test 2: Send telemetry for asset 4 (payment processing)
print("=== Test 2: Telemetry for asset 4 ===")
resp = client.post('/api/v1/telemetry', json={
    "timestamp": "2026-01-15T10:35:00Z",
    "asset_id": 4,
    "event_type": "threat_likelihood_increased",
    "severity": 70,
    "vulnerability_id": "VULN-005",
    "threat_likelihood": 0.8,
    "control_effectiveness": 0.4,
    "source": "EDR-01"
})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Updated risk score: {data['updated_risk_assessment']['risk_score']}")
    print(f"Risk level: {data['updated_risk_assessment']['risk_level']}")
    print(f"ALE: {data['updated_risk_assessment']['ale']}")

print()

# Test 3: Send malformed telemetry (missing asset_id)
print("=== Test 3: Missing asset_id ===")
resp = client.post('/api/v1/telemetry', json={
    "event_type": "test",
    "severity": 50
})
print(f"Status: {resp.status_code}")
if resp.status_code == 400:
    print(f"Error: {resp.json().get('detail')}")

print()

# Test 4: Send telemetry for non-existent asset
print("=== Test 4: Non-existent asset ===")
resp = client.post('/api/v1/telemetry', json={
    "asset_id": 999,
    "event_type": "test",
    "severity": 50
})
print(f"Status: {resp.status_code}")
if resp.status_code == 400:
    print(f"Error: {resp.json().get('detail')}")

print()

# Test 5: Send telemetry with no fields (just asset_id)
print("=== Test 5: Minimal telemetry ===")
resp = client.post('/api/v1/telemetry', json={
    "asset_id": 1
})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Message: {data['message']}")
    print(f"Risk score: {data['updated_risk_assessment']['risk_score']}")

print()

# Test 6: Send telemetry with severity out of range
print("=== Test 6: Severity 0 ===")
resp = client.post('/api/v1/telemetry', json={
    "asset_id": 1,
    "event_type": "test",
    "severity": 0,
    "threat_likelihood": 0,
    "control_effectiveness": 0
})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"Severity normalized: {data['stored_event']['severity']}")
    print(f"Likelihood normalized: {data['stored_event']['threat_likelihood']}")
    print(f"Control effectiveness normalized: {data['stored_event']['control_effectiveness']}")

print()
print("All tests complete!")