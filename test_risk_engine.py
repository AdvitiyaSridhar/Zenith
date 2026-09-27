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

from urllib.request import urlopen
import json

def get_endpoint(path):
    try:
        r = urlopen(f'http://127.0.0.1:8000{path}')
        body = json.loads(r.read().decode())
        return r.status, body
    except Exception as e:
        return None, str(e)

# Get a risk assessment to see the data structure
status, assessments = get_endpoint('/api/v1/risk-assessments')
if assessments and len(assessments) > 0:
    a1 = assessments[0]
    print('=== First risk assessment ===')
    for k, v in a1.items():
        print(f'  {k}: {v}')
    
    # Get the associated asset
    status, asset = get_endpoint(f'/api/v1/assets/{a1["asset_id"]}')
    if asset:
        print('\\n=== Associated asset ===')
        for k, v in asset.items():
            print(f'  {k}: {v}')
    
    # Get risk drivers
    status, drivers = get_endpoint('/api/v1/risk/drivers/1')
    if drivers:
        print('\\n=== Risk drivers for asset 1 ===')
        for k, v in drivers.items():
            if k != 'asset_id':
                print(f'  {k}: {v}')

# Check all risk assessments sample
print('\\n=== Sample risk assessments (first 3) ===')
for a in assessments[:3]:
    print(f'  ID={a.get("id")}, asset_id={a.get("asset_id")}, likelihood={a.get("current_likelihood")}, control_eff={a.get("current_control_effectiveness")}, risk_score={a.get("current_risk_score")}, loss={a.get("expected_loss")}')