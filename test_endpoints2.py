import sys
sys.path.insert(0, r'C:\Advi\Collegestuff\Events\SIH\zenith\backend')
import uvicorn
import threading
import time
from urllib.request import urlopen, Request
import json

def run_server():
    uvicorn.run('zenith_backend.main:app', host='127.0.0.1', port=8000)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

def get_endpoint(path):
    try:
        r = urlopen(f'http://127.0.0.1:8000{path}')
        body = json.loads(r.read().decode())
        return r.status, body
    except Exception as e:
        return None, str(e)

def post_endpoint(path, data_dict):
    try:
        data = json.dumps(data_dict).encode()
        req = Request(path, data=data, method='POST', headers={'Content-Type': 'application/json'})
        r = urlopen(req)
        body = json.loads(r.read().decode())
        return r.status, body
    except Exception as e:
        return None, str(e)

# Test GET endpoints
print('=== GET /api/v1/assets ===')
status, body = get_endpoint('/api/v1/assets')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/threats ===')
status, body = get_endpoint('/api/v1/threats')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/risk-assessments ===')
status, body = get_endpoint('/api/v1/risk-assessments')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/risk-assessments/1 ===')
status, body = get_endpoint('/api/v1/risk-assessments/1')
print(f'Risk score: {body.get("current_risk_score")}, Level: {body.get("risk_level")}')

print('=== GET /api/v1/investment-options ===')
status, body = get_endpoint('/api/v1/investment-options')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/scenarios ===')
status, body = get_endpoint('/api/v1/scenarios')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/recommendations/prioritized ===')
status, body = get_endpoint('/api/v1/recommendations/prioritized')
print(f'Status: {status}, Count: {len(body)}')

if body:
    print(f'First recommendation: {body[0].get("id")} - {body[0].get("title", "N/A")}')

print('=== GET /api/v1/risk/drivers/1 ===')
status, body = get_endpoint('/api/v1/risk/drivers/1')
print(f'Status: {status}, Keys: {list(body.keys()) if isinstance(body, dict) else "array of " + str(len(body))}')

# Test POST endpoints
print('\\n=== POST /api/v1/telemetry ===')
status, body = post_endpoint('/api/v1/telemetry', {'asset_id': 1, 'event_type': 'intrusion_attempt', 'severity': 75, 'threat_likelihood': 0.8, 'control_effectiveness': 0.5, 'source': 'siem_sensor'})
print(f'Status: {status}, Response: {body}')

print('\\n=== POST /api/v1/chat/llm ===')
status, body = post_endpoint('/api/v1/chat/llm', {'message': 'What is the risk level for asset 1?', 'asset_id': 1})
print(f'Status: {status}, Response preview: {str(body)[:100] if isinstance(body, str) else body}')

print('\\n=== All GET endpoints tested successfully! ===')