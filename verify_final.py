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
    ('GET', f'{base}/api/v1/risk/calculate/1'),
    ('GET', f'{base}/api/v1/risk/drivers/1'),
    ('GET', f'{base}/api/v1/recommendations/prioritized'),
    ('GET', f'{base}/api/v1/recommendations/investment/50000'),
]

print('=== FINAL VERIFICATION ===')
all_ok = True
for method, url in endpoints:
    status, text = fetch(method, url)
    ok = status == 200
    all_ok = all_ok and ok
    print(f'  {method} {url}: Status {status}' + (' ✅' if ok else ' ❌'))

print(f'\nAll endpoints: {"PASS ✅" if all_ok else "FAIL ❌"}')