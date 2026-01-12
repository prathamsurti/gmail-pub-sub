import React, { useState } from 'react';

const AGENT_API_URL = 'http://localhost:8001';

const testScenarios = [
  {
    id: 1,
    name: 'Hot Lead (Enterprise Inquiry)',
    email: {
      email_sender: 'cto@bigcorp.com',
      email_subject: 'Urgent: Enterprise Pricing for 1000 Users',
      email_body: `Hi,

We're looking to deploy your solution for our entire organization (1000+ users).
We need this by end of month. Can you send pricing and schedule a call ASAP?

Thanks,
John Smith
CTO, BigCorp Inc.`,
      email_id: 'test_msg_001',
      thread_id: 'test_thread_001'
    },
    expected: 'Hot Lead - Should draft reply'
  },
  {
    id: 2,
    name: 'Spam/Marketing Email',
    email: {
      email_sender: 'noreply@marketing.com',
      email_subject: '🎉 You\'ve Won a Free iPhone!',
      email_body: `Congratulations! You've been selected as a winner!

Click here to claim your FREE iPhone 15 Pro Max now!
Limited time offer. Act fast!`,
      email_id: 'test_msg_002',
      thread_id: 'test_thread_002'
    },
    expected: 'Spam - Should ignore'
  },
  {
    id: 3,
    name: 'Warm Lead (General Inquiry)',
    email: {
      email_sender: 'startup@example.com',
      email_subject: 'Question about your product',
      email_body: `Hi,

I came across your website and I'm interested in learning more about your product.
Could you send me some information?

Best regards,
Sarah`,
      email_id: 'test_msg_003',
      thread_id: 'test_thread_003'
    },
    expected: 'Warm Lead - Should draft reply'
  }
];

function AgentTester({ showStatus }) {
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);

  const runSingleTest = async (scenario) => {
    setSelectedTest(scenario.id);
    showStatus(`🧪 Testing: ${scenario.name}...`, 'info');

    try {
      const response = await fetch(`${AGENT_API_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scenario.email),
        timeout: 30000
      });

      if (response.ok) {
        const result = await response.json();
        const testResult = {
          scenario: scenario.name,
          success: true,
          isLead: result.analysis.is_lead,
          classification: result.analysis.classification,
          confidence: result.analysis.confidence,
          action: result.action,
          reasoning: result.analysis.reasoning,
          draft: result.draft,
          timestamp: new Date().toLocaleTimeString()
        };
        
        setTestResults(prev => [testResult, ...prev]);
        showStatus(`✅ Test complete: ${scenario.name}`, 'success');
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      const testResult = {
        scenario: scenario.name,
        success: false,
        error: error.message,
        timestamp: new Date().toLocaleTimeString()
      };
      setTestResults(prev => [testResult, ...prev]);
      showStatus(`❌ Test failed: ${error.message}`, 'error');
    } finally {
      setSelectedTest(null);
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTestResults([]);
    showStatus('🚀 Running all agent tests...', 'info');

    for (const scenario of testScenarios) {
      await runSingleTest(scenario);
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setIsRunning(false);
    showStatus('✅ All tests complete!', 'success');
  };

  const clearResults = () => {
    setTestResults([]);
    showStatus('Cleared test results', 'info');
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🤖 Agent Testing Suite</h2>
        <p style={styles.subtitle}>Test the AI email agent with predefined scenarios</p>
      </div>

      <div style={styles.controls}>
        <button 
          onClick={runAllTests} 
          disabled={isRunning}
          style={{...styles.button, ...styles.primaryButton}}
        >
          {isRunning ? '⏳ Running Tests...' : '🚀 Run All Tests'}
        </button>
        <button 
          onClick={clearResults}
          style={{...styles.button, ...styles.secondaryButton}}
        >
          🗑️ Clear Results
        </button>
      </div>

      <div style={styles.scenariosGrid}>
        {testScenarios.map((scenario) => (
          <div key={scenario.id} style={styles.scenarioCard}>
            <h3 style={styles.scenarioTitle}>{scenario.name}</h3>
            <div style={styles.scenarioDetails}>
              <p><strong>From:</strong> {scenario.email.email_sender}</p>
              <p><strong>Subject:</strong> {scenario.email.email_subject}</p>
              <p><strong>Expected:</strong> {scenario.expected}</p>
            </div>
            <button
              onClick={() => runSingleTest(scenario)}
              disabled={isRunning || selectedTest === scenario.id}
              style={{...styles.button, ...styles.testButton}}
            >
              {selectedTest === scenario.id ? '⏳ Testing...' : '🧪 Test This'}
            </button>
          </div>
        ))}
      </div>

      {testResults.length > 0 && (
        <div style={styles.results}>
          <h3 style={styles.resultsTitle}>📊 Test Results</h3>
          {testResults.map((result, index) => (
            <div 
              key={index} 
              style={{
                ...styles.resultCard,
                ...(result.success ? styles.resultSuccess : styles.resultError)
              }}
            >
              <div style={styles.resultHeader}>
                <span style={styles.resultScenario}>{result.scenario}</span>
                <span style={styles.resultTime}>{result.timestamp}</span>
              </div>

              {result.success ? (
                <div style={styles.resultDetails}>
                  <div style={styles.resultRow}>
                    <span className="label">Is Lead:</span>
                    <span style={{...styles.badge, ...(result.isLead ? styles.badgeSuccess : styles.badgeWarning)}}>
                      {result.isLead ? '✅ Yes' : '❌ No'}
                    </span>
                  </div>
                  {result.classification && (
                    <div style={styles.resultRow}>
                      <span className="label">Classification:</span>
                      <span style={styles.badge}>{result.classification}</span>
                    </div>
                  )}
                  {result.confidence && (
                    <div style={styles.resultRow}>
                      <span className="label">Confidence:</span>
                      <span>{(result.confidence * 100).toFixed(1)}%</span>
                    </div>
                  )}
                  <div style={styles.resultRow}>
                    <span className="label">Action:</span>
                    <span style={styles.badge}>{result.action || 'N/A'}</span>
                  </div>
                  {result.reasoning && (
                    <div style={styles.resultRow}>
                      <span className="label">Reasoning:</span>
                      <span style={styles.reasoning}>{result.reasoning}</span>
                    </div>
                  )}
                  {result.draft && (
                    <div style={styles.draftSection}>
                      <h4 style={styles.draftTitle}>📝 Generated Draft:</h4>
                      <p><strong>To:</strong> {result.draft.to}</p>
                      <p><strong>Subject:</strong> {result.draft.subject}</p>
                      <div style={styles.draftBody}>
                        <strong>Body:</strong>
                        <div dangerouslySetInnerHTML={{ __html: result.draft.body }} />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={styles.errorMessage}>
                  ❌ Error: {result.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={styles.info}>
        <p><strong>ℹ️ Info:</strong> Agent service must be running on <code>localhost:8001</code></p>
        <p>Start with: <code>cd gmail_agent && uvicorn api:app --port 8001</code></p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  header: {
    textAlign: 'center',
    marginBottom: '30px'
  },
  title: {
    fontSize: '28px',
    marginBottom: '10px',
    color: '#333'
  },
  subtitle: {
    color: '#666',
    fontSize: '16px'
  },
  controls: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    marginBottom: '30px'
  },
  button: {
    padding: '12px 24px',
    fontSize: '16px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: '600',
    transition: 'all 0.2s'
  },
  primaryButton: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white'
  },
  secondaryButton: {
    background: '#f0f0f0',
    color: '#333'
  },
  testButton: {
    background: '#4CAF50',
    color: 'white',
    width: '100%',
    marginTop: '10px'
  },
  scenariosGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  scenarioCard: {
    border: '2px solid #e0e0e0',
    borderRadius: '12px',
    padding: '20px',
    background: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },
  scenarioTitle: {
    fontSize: '18px',
    marginBottom: '15px',
    color: '#333'
  },
  scenarioDetails: {
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.6'
  },
  results: {
    marginTop: '30px'
  },
  resultsTitle: {
    fontSize: '22px',
    marginBottom: '20px',
    color: '#333'
  },
  resultCard: {
    border: '2px solid',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '15px',
    background: 'white'
  },
  resultSuccess: {
    borderColor: '#4CAF50',
    background: '#f1f8f4'
  },
  resultError: {
    borderColor: '#f44336',
    background: '#fef5f5'
  },
  resultHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '1px solid #e0e0e0'
  },
  resultScenario: {
    fontWeight: '600',
    fontSize: '16px'
  },
  resultTime: {
    color: '#999',
    fontSize: '14px'
  },
  resultDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  resultRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '14px'
  },
  badge: {
    padding: '4px 12px',
    borderRadius: '12px',
    background: '#e0e0e0',
    fontSize: '13px',
    fontWeight: '500'
  },
  badgeSuccess: {
    background: '#4CAF50',
    color: 'white'
  },
  badgeWarning: {
    background: '#ff9800',
    color: 'white'
  },
  reasoning: {
    flex: 1,
    fontStyle: 'italic',
    color: '#555'
  },
  draftSection: {
    marginTop: '15px',
    padding: '15px',
    background: 'white',
    borderRadius: '8px',
    border: '1px solid #e0e0e0'
  },
  draftTitle: {
    fontSize: '16px',
    marginBottom: '10px',
    color: '#333'
  },
  draftBody: {
    marginTop: '10px',
    padding: '10px',
    background: '#f9f9f9',
    borderRadius: '6px',
    fontSize: '13px',
    maxHeight: '200px',
    overflow: 'auto'
  },
  errorMessage: {
    color: '#f44336',
    fontWeight: '500'
  },
  info: {
    marginTop: '30px',
    padding: '15px',
    background: '#e3f2fd',
    borderRadius: '8px',
    fontSize: '14px',
    color: '#1976d2'
  }
};

export default AgentTester;
