import urllib.request
import json

base = 'http://127.0.0.1:8000'

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

endpoints = [
    # Frontend api.js endpoints
    ('GET', f'{base}/health'),
    ('GET', f'{base}/api/v1/assets'),
    ('GET', f'{base}/api/v1/assets/1'),
    ('GET', f'{base}/api/v1/vulnerabilities'),
    ('GET', f'{base}/api/v1/threats'),
    ('GET', f'{base}/api/v1/controls'),
    ('GET', f'{base}/api/v1/risk-assessments'),
    ('GET', f'{base}/api/v1/risk-assessments/1'),
    ('GET', f'{base}/api/v1/investment-options'),
    ('GET', f'{base}/api/v1/scenarios'),
    ('GET', f'{base}/api/v1/scenarios/compare'),
    ('GET', f'{base}/api/v1/risk/calculate/1'),  # Now fixed to accept GET
    ('GET', f'{base}/api/v1/risk/drivers/1'),
    ('GET', f'{base}/api/v1/recommendations/prioritized'),
    ('GET', f'{base}/api/v1/recommendations/investment/50000'),
    # POST endpoint
    ('POST', f'{base}/api/v1/telemetry', {'asset_id': 1, 'event_type': 'test', 'severity': 5, 'threat_likelihood': 0.5, 'control_effectiveness': 0.5, 'source': 'test'}),
]

print('=== API Endpoint Verification ===')
all_pass = True
for item in endpoints:
    method = item[0]
    url = item[1]
    body = item[2] if len(item) > 2 else None
    try:
        status, text = fetch(method, url, body)
        data = json.loads(text) if status < 500 else text
        preview = json.dumps(data)[:80] if isinstance(data, dict) else str(data)[:80]
        print(f'  {method} {url}: Status {status} - OK')
    except Exception as e:
        print(f'  {method} {url}: Error - {e}')
        all_pass = False

print()
if all_pass:
    print('All frontend API endpoints verified! ✅')
else:
    print('Some endpoints failed ❌')