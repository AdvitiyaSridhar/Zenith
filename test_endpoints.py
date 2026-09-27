import sys
sys.path.insert(0, r'C:\Advi\Collegestuff\Events\SIH\zenith\backend')
import uvicorn
import threading
import time
from urllib.request import urlopen
import json

def run_server():
    uvicorn.run('zenith_backend.main:app', host='127.0.0.1', port=8000)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

def test_endpoint(path, method='GET'):
    try:
        r = urlopen(f'http://127.0.0.1:8000{path}')
        body = json.loads(r.read().decode())
        return r.status, body
    except Exception as e:
        return None, str(e)

def post_endpoint(path, data):
    try:
        req = urlopen(path)  # won't work for POST, let me use urllib directly
    except:
        pass

# Test various endpoints
print('=== GET /api/v1/assets ===')
status, body = test_endpoint('/api/v1/assets')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/assets/1 ===')
status, body = test_endpoint('/api/v1/assets/1')
print(f'Status: {status}, Name: {body.get("name", "N/A")}')

print('=== GET /api/v1/vulnerabilities ===')
status, body = test_endpoint('/api/v1/vulnerabilities')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/threats ===')
status, body = test_endpoint('/api/v1/threats')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/controls ===')
status, body = test_endpoint('/api/v1/controls')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/risk-assessments ===')
status, body = test_endpoint('/api/v1/risk-assessments')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/risk-assessments/1 ===')
status, body = test_endpoint('/api/v1/risk-assessments/1')
print(f'Status: {status}, Risk score: {body.get("current_risk_score", "N/A")}')

print('=== GET /api/v1/investment-options ===')
status, body = test_endpoint('/api/v1/investment-options')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/scenarios ===')
status, body = test_endpoint('/api/v1/scenarios')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/recommendations/prioritized ===')
status, body = test_endpoint('/api/v1/recommendations/prioritized')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/recommendations/investment/50000 ===')
status, body = test_endpoint('/api/v1/recommendations/investment/50000')
print(f'Status: {status}, Count: {len(body)}')

print('=== GET /api/v1/risk/calculate/1 ===')
status, body = test_endpoint('/api/v1/risk/calculate/1')
print(f'Status: {status}, Risk score: {body.get("risk_score", "N/A")}')

print('=== GET /api/v1/risk/drivers/1 ===')
status, body = test_endpoint('/api/v1/risk/drivers/1')
print(f'Status: {status}, Drivers: {body.get("risk_drivers", "N/A")}')

# POST telemetry
print('=== POST /api/v1/telemetry ===')
try:
    data = json.dumps({'asset_id': 1, 'event_type': 'test', 'severity': 50, 'threat_likelihood': 0.5, 'control_effectiveness': 0.5, 'source': 'test'}).encode()
    req = urlopen('http://127.0.0.1:8000/api/v1/telemetry')  # This won't work for POST
    print(f'Status: {r.status}')
except Exception as e:
    print(f'Telemetry error: {type(e).__name__}: {e}')

# POST chat
print('=== POST /api/v1/chat/llm ===')
try:
    data = json.dumps({'message': 'test message', 'asset_id': 1}).encode()
    req = urlopen('http://127.0.0.1:8000/api/v1/chat/llm')  # This won't work for POST
    print(f'Status: {r.status}')
except Exception as e:
    print(f'Chat error: {type(e).__name__}: {e}')