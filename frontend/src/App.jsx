import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';

function riskLevelColor(level) {
  if (!level) return '#6b6375';
  switch (level) {
    case 'critical': return '#dc2626';
    case 'high': return '#f59e0b';
    case 'medium': return '#eab308';
    case 'low': return '#10b981';
    default: return '#6b6375';
  }
}

function App() {
  const [telemetry, setTelemetry] = useState({
    asset_id: '',
    event_type: '',
    severity: '',
    threat_likelihood: '',
    control_effectiveness: '',
    source: ''
  });
  const [telemetryResult, setTelemetryResult] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTelemetry({ ...telemetry, [name]: value });
  };

  const ingestTelemetry = async () => {
    import('./api.js').then(module => {
      const { api } = module;
      api.ingestTelemetry(telemetry).then(result => {
        setTelemetryResult(result);
        // Reset form after 3 seconds
        setTimeout(() => setTelemetryResult(null), 3000);
      });
    });
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/chat/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content, asset_id: parseInt(telemetry.asset_id) || undefined })
      });
      const data = await res.json();
      
      if (data.response) {
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setChatMessages(prev => [...prev, { role: 'assistant', content: 'No response from LLM.' }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error contacting backend: ' + err.message }]);
    }
  };

  return (
    <div>
      <h1>SIH26105 Cyber Risk Platform</h1>

      {/* Telemetry Ingestion Panel */}
      <div style={{
        background: '#f8f9fa', padding: '20px', borderRadius: '8px',
        marginBottom: '24px', border: '1px solid #e5e4e7'
      }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#343a40' }}>Real-time Telemetry Ingestion</h3>
        <form style={{ display: 'grid', gap: '12px' }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Asset ID</label>
            <input
              type="number"
              name="asset_id"
              value={telemetry.asset_id}
              onChange={handleChange}
              placeholder="e.g., 1"
              style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
              required
            />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Event Type</label>
            <input
              type="text"
              name="event_type"
              value={telemetry.event_type}
              onChange={handleChange}
              placeholder="e.g., intrusion_attempt"
              style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
              required
            />
          </div>
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: '1fr 1fr' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Severity (0-100)</label>
              <input
                type="number"
                name="severity"
                value={telemetry.severity}
                onChange={handleChange}
                placeholder="e.g., 75"
                style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Threat Likelihood (0-1)</label>
              <input
                type="number"
                name="threat_likelihood"
                value={telemetry.threat_likelihood}
                onChange={handleChange}
                placeholder="e.g., 0.75"
                style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Control Effectiveness (0-1)</label>
              <input
                type="number"
                name="control_effectiveness"
                value={telemetry.control_effectiveness}
                onChange={handleChange}
                placeholder="e.g., 0.5"
                style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
                required
              />
            </div>
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: '500' }}>Source</label>
            <input
              type="text"
              name="source"
              value={telemetry.source}
              onChange={handleChange}
              placeholder="e.g., siem_sensor"
              style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px', width: '100%' }}
            />
          </div>
          <button
            type="button"
            onClick={ingestTelemetry}
            style={{
              background: '#aa3bff', color: 'white',
              border: 'none', borderRadius: '4px', padding: '8px 16px',
              cursor: 'pointer', width: '100%', fontSize: '14px',
              marginTop: '8px'
            }}
          >
            Ingest Telemetry
          </button>
        </form>
{telemetryResult && (
          <div style={{
            marginTop: '16px', padding: '16px', borderRadius: '8px',
            background: '#d4edda', color: '#155724', border: '1px solid #c3e6cb'
          }}>
            <h4>✅ Telemetry Ingested Successfully</h4>
            <pre style={{ margin: '8px 0', fontSize: '12px', whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(telemetryResult, null, 2)}
            </pre>
            <p style={{ margin: '0', fontSize: '12px', color: '#155724' }}>
              Risk score: <strong>{telemetryResult.updated_risk_assessment.risk_score}</strong>,
              Level: <strong>{telemetryResult.updated_risk_assessment.risk_level}</strong>
            </p>
          </div>
        )}
        {/* Chat Interface */}
        <div style={{
          marginTop: '24px', borderTop: '1px solid #e5e4e7', paddingTop: '24px'
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#343a40' }}>LLM Risk Consultant</h3>
          <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #dee2e6', borderRadius: '8px', padding: '16px', background: '#f8f9fa', marginBottom: '16px' }}>
            {chatMessages.map((msg, idx) => (
              <div key={idx} style={{
                padding: '8px 12px', borderRadius: '12px', margin: '8px 0',
                maxWidth: '80%', wordBreak: 'break-all'
              }}>
                <strong style={{ marginRight: '8px' }}>{msg.role}:</strong>
                <span dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br>') }}></span>
              </div>
            ))}
          </div>
          <div style={{ display: 'grid', gap: '8px', gridTemplateColumns: '1fr auto' }}>
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)} placeholder="Ask about risk scenarios..." style={{ padding: '8px', border: '1px solid #dee2e6', borderRadius: '4px' }}
            />
            <button
              onClick={sendChatMessage}
              style={{
                background: '#aa3bff', color: 'white', border: 'none', borderRadius: '4px',
                padding: '8px 16px', cursor: 'pointer', fontSize: '14px'
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    );
}

export default App;