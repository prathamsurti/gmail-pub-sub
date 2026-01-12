import React, { useState, useEffect } from 'react';
import LeadsDashboard from './LeadsDashboard';
import AgentTester from './AgentTester';
import { CookieManager } from '../utils/cookieManager';

function Dashboard({ userInfo, onLogout, showStatus, apiBaseUrl }) {
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [newLead, setNewLead] = useState(null); // For push updates
  const [activeTab, setActiveTab] = useState('leads'); // 'leads' or 'agents'

  useEffect(() => {
    // Check existing session
    const sessionId = CookieManager.get('session_id');

    // Automatically sync on load to ensure new emails are processed
    // User requested only "last 2 emails (as history)" check on startup
    if (sessionId) {
      syncWithGmail(true, 2);
      setupGmailWatch(sessionId);
      setupSSE(sessionId);
    }

    return () => {
      if (window.eventSource) {
        window.eventSource.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setupSSE = (sessionId) => {
    if (window.eventSource) {
      window.eventSource.close();
    }

    const eventSource = new EventSource(`${apiBaseUrl}/events?session_id=${sessionId}`);
    window.eventSource = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📧 Real-time notification:', data);

      if (data.type === 'new_lead') {
        showStatus('✨ New Lead Analyzed!', 'success');
        // Push update instead of full refresh
        setNewLead(data.data);
      } else if (data.type === 'new_email') {
        // Fallback for raw emails if backend sends them
        console.log('New email received, syncing...');
        showStatus('📧 New email detected! Analyzing...', 'info');
        syncWithGmail(true, 1); // This will trigger analysis for just the new one
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
    };
  };

  const syncWithGmail = async (silent = false, maxResults = 10) => {
    const sessionId = CookieManager.get('session_id');
    if (!sessionId) {
      showStatus('Session expired. Please sign in again.', 'error');
      onLogout();
      return;
    }

    if (!silent) setIsLoading(true);

    try {
      // process_leads=true triggers the agent for any unread emails found
      const response = await fetch(`${apiBaseUrl}/gmail/sync?session_id=${sessionId}&process_leads=true&max_results=${maxResults}`);

      if (response.ok) {
        const data = await response.json();
        if (!silent) {
          showStatus(`Sync complete. Analyzed ${data.messages?.length || 0} emails`, 'success');
        }
        // Only trigger full refresh if it was a manual sync (not silent)
        if (!silent) {
          setLastUpdate(Date.now());
        }
      } else {
        if (!silent) showStatus('Sync failed', 'error');
      }
    } catch (error) {
      console.error('Sync error:', error);
      if (!silent) showStatus('Failed to sync', 'error');
    } finally {
      if (!silent) setIsLoading(false);
    }
  };

  const setupGmailWatch = async (sessionId) => {
    try {
      await fetch(`${apiBaseUrl}/gmail/watch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          topic_name: 'projects/jaano-gmail/topics/gmail-notifications'
        })
      });
    } catch (error) {
      console.error('Error setting up Gmail watch:', error);
    }
  };

  return (
    <div id="dashboardSection" className="section">
      <div className="user-info">
        <div className="user-details">
          <h3>Welcome, {userInfo.name}!</h3>
          <p>{userInfo.email}</p>
        </div>
        <button id="signOutBtn" className="sign-out-btn" onClick={onLogout}>
          Sign Out
        </button>
      </div>

      {/* Tab Navigation */}
      <div style={styles.tabContainer}>
        <button
          onClick={() => setActiveTab('leads')}
          style={{
            ...styles.tab,
            ...(activeTab === 'leads' ? styles.activeTab : {})
          }}
        >
          📊 Leads Dashboard
        </button>
        <button
          onClick={() => setActiveTab('agents')}
          style={{
            ...styles.tab,
            ...(activeTab === 'agents' ? styles.activeTab : {})
          }}
        >
          🤖 Agent Testing
        </button>
      </div>

      {/* Leads Tab */}
      {activeTab === 'leads' && (
        <>
          <div className="sync-section">
            <button
              id="syncBtn"
              className="sync-btn"
              onClick={() => syncWithGmail(false, 10)}
              disabled={isLoading}
            >
              {isLoading ? '🔄 Analyzing Inbox...' : '🔄 Sync & Analyze Inbox'}
            </button>
            <p style={styles.syncHint}>
              Sync checks for new emails and runs AI analysis
            </p>
          </div>

          <LeadsDashboard
            showStatus={showStatus}
            apiBaseUrl={apiBaseUrl}
            lastUpdate={lastUpdate}
            newLead={newLead}
          />
        </>
      )}

      {/* Agent Testing Tab */}
      {activeTab === 'agents' && (
        <AgentTester showStatus={showStatus} />
      )}
    </div>
  );
}

const styles = {
  tabContainer: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    borderBottom: '2px solid #e0e0e0'
  },
  tab: {
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '600',
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    borderBottom: '3px solid transparent',
    transition: 'all 0.2s',
    color: '#666'
  },
  activeTab: {
    borderBottom: '3px solid #667eea',
    color: '#667eea'
  },
  syncHint: {
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '4px',
    marginLeft: '10px',
    display: 'inline-block'
  }
};

export default Dashboard;
