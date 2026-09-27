import urllib.request
import json

base = 'http://127.0.0.1:8000'
endpoints = [
    '/health',
    '/api/v1/assets',
    '/api/v1/assets/1',
    '/api/v1/risk/calculate/1',
    '/api/v1/risk/drivers/1',
    '/api/v1/recommendations/prioritized',
]

print('=== BACKEND VERIFICATION ===')
for ep in endpoints:
    try:
        url = base + ep
        r = urllib.request.urlopen(url)
        status = r.status
        data = json.loads(r.read().decode())
        preview = json.dumps(data)[:60] if isinstance(data, dict) else str(data)[:60]
        print(f'  GET {ep}: {status} - {preview}')
    except Exception as e:
        print(f'  GET {ep}: Error - {e}')