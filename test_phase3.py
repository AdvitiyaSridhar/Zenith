import urllib.request
import json

base = 'http://127.0.0.1:8000/api/v1'

def fetch(method, url, body=None):
    if body:
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# Test POST /investment/optimize
print('=== POST /api/v1/investment/optimize/50000 ===')
status, text = fetch('POST', f'{base}/optimize/50000')
data = json.loads(text)
print(f'Status: {status}')
print(f'Total cost: {data.get("total_cost")}')
print(f'Expected risk reduction: {data.get("expected_risk_reduction")}')
print(f'ROI %: {data.get("roi_percent")}')
print(f'Baseline ALE: {data.get("baseline_ale")}')

# Test POST /chat/llm
print()
print('=== POST /api/v1/chat/llm ===')
status, text = fetch('POST', f'{base}/chat/llm', {'message': 'test risk', 'asset_id': 1})
data = json.loads(text)
print(f'Status: {status}')
print(f'Status field: {data.get("status")}')
print(f'Message: {data.get("message", "")[:100]}')

# Test GET vs POST /risk/calculate
print()
print('=== GET http://127.0.0.1:8000/risk/calculate/1 ===')
status, text = fetch('GET', 'http://127.0.0.1:8000/risk/calculate/1')
print(f'Status: {status}')

print()
print('=== POST http://127.0.0.1:8000/risk/calculate/1 ===')
status, text = fetch('POST', 'http://127.0.0.1:8000/risk/calculate/1')
data = json.loads(text)
print(f'Status: {status}')
if status == 200:
    print(f'risk_score: {data.get("risk_score")}')
    print(f'expected_loss: {data.get("expected_loss")}')
    print(f'risk_level: {data.get("risk_level")}')

# Test /risk/assessment (GET)
print()
print('=== GET /risk/assessment/1 ===')
status, text = fetch('GET', 'http://127.0.0.1:8000/risk/assessment/1')
data = json.loads(text)
print(f'Status: {status}')
if status == 200:
    print(f'risk_score: {data.get("risk_score")}')
    print(f'expected_loss: {data.get("expected_loss")}')

# Test /risk/drivers (GET)
print()
print('=== GET /risk/drivers/1 ===')
status, text = fetch('GET', 'http://127.0.0.1:8000/risk/drivers/1')
data = json.loads(text)
print(f'Status: {status}')
if status == 200:
    print(f'Keys: {list(data.keys())}')
    if 'risk_drivers' in data:
        print(f'risk_drivers: {data["risk_drivers"]}')

# Test /telemetry POST
print()
print('=== POST /telemetry ===')
status, text = fetch('POST', 'http://127.0.0.1:8000/telemetry', {
    'asset_id': 1,
    'event_type': 'test',
    'severity': 5,
    'threat_likelihood': 0.5,
    'control_effectiveness': 0.5,
    'source': 'test'
})
data = json.loads(text)
print(f'Status: {status}')
print(f'Response: {text[:200]}')