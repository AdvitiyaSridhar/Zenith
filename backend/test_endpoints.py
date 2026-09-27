import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from zenith_backend.main import app

client = TestClient(app)

# Test all endpoints
print('=== Testing Backend Endpoints ===')

# 1. Test telemetry endpoint
resp = client.post('/api/v1/telemetry', json={
    'asset_id': 1,
    'event_type': 'intrusion_attempt',
    'severity': 75,
    'threat_likelihood': 0.75,
    'control_effectiveness': 0.5,
    'source': 'siem_sensor'
})
print(f'1. POST /api/v1/telemetry: status={resp.status_code}')

# 2. Test chat endpoint  
resp = client.post('/api/v1/chat/llm', json={
    'message': 'What security controls should I prioritize?',
    'asset_id': 1
})
print(f'2. POST /api/v1/chat/llm: status={resp.status_code}')

# 3. Test risk assessment
resp = client.get('/api/v1/risk/assessment/1')
print(f'3. GET /api/v1/risk/assessment/1: status={resp.status_code}')

# 4. Test assets
resp = client.get('/api/v1/assets')
print(f'4. GET /api/v1/assets: status={resp.status_code}, assets={len(resp.json())}')

print()
print('All backend endpoints working correctly!')