import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from zenith_backend.main import app

client = TestClient(app)

# Test the chat endpoint
resp = client.post('/api/v1/chat/llm', json={
    'message': 'What security controls should I prioritize to reduce risk?',
    'asset_id': 1
})
print('Status:', resp.status_code)
data = resp.json()
print('Response type:', type(data['response']).__name__)
print('Status:', data['status'])
print('Current risk level:', data['current_risk_level'])
print('Risk score:', data['risk_score'])
print('Selected controls:', data['selected_controls'])
print('Investment:', data['total_investment'])
print('Risk reduction %:', data['risk_reduction_pct'])
print()
print('LLM Response:')
print(data['response'])