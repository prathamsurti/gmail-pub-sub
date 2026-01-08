import React, { useState, useEffect } from 'react';
import EmailList from './EmailList';
import { CookieManager } from '../utils/cookieManager';
import { StateManager } from '../utils/stateManager';

function Dashboard({ userInfo, onLogout, showStatus, apiBaseUrl }) {
  const [emails, setEmails] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Load cached emails on mount
    loadCachedEmails();
    
    // Automatically sync on load
    syncWithGmail(true);

    const sessionId = CookieManager.get('session_id');
    
    // Set up Gmail watch for Pub/Sub notifications
    setupGmailWatch(sessionId);
    
    // Set up Server-Sent Events for real-time notifications
    let eventSource;
    if (sessionId) {
      eventSource = new EventSource(`${apiBaseUrl}/events?session_id=${sessionId}`);
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('📧 Real-time notification:', data);
        
        if (data.type === 'new_email') {
          showStatus('📬 New email received! Syncing...', 'info');
          syncWithGmail(true);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventSource.close();
      };
    }

    // Set up global notification handler (backup)
    window.handleNewEmailNotification = (data) => {
      console.log('New email notification received:', data);
      showStatus('📬 New email received! Syncing...', 'info');
      syncWithGmail(true);
    };

    return () => {
      if (eventSource) {
        eventSource.close();
      }
      delete window.handleNewEmailNotification;
    };
  }, []);

  const loadCachedEmails = () => {
    const cachedEmails = StateManager.loadEmails();
    const lastUpdateTime = StateManager.getLastUpdate();

    if (cachedEmails && cachedEmails.length > 0) {
      setEmails(cachedEmails);
      setLastUpdate(lastUpdateTime);
    }
  };

  const syncWithGmail = async (silent = false) => {
    const sessionId = CookieManager.get('session_id');
    if (!sessionId) {
      showStatus('Session expired. Please sign in again.', 'error');
      onLogout();
      return;
    }

    console.log('Starting Gmail sync...', { sessionId, silent });

    if (!silent) {
      setIsLoading(true);
    }

    try {
      const response = await fetch(`${apiBaseUrl}/gmail/sync?session_id=${sessionId}`);
      console.log('Sync response status:', response.status);

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('Sync response data:', data);

      if (data.messages && Array.isArray(data.messages)) {
        setEmails(data.messages);
        StateManager.saveEmails(data.messages);
        setLastUpdate(new Date().toISOString());

        // Update access token if it was refreshed
        if (data.new_access_token) {
          console.log('🔄 Token was refreshed, updating cookie');
          CookieManager.set('google_access_token', data.new_access_token, 7);
        }

        if (!silent) {
          showStatus(`Synced ${data.messages.length} unread emails`, 'success');
        }

        // Update unread count
        await getUnreadCount();
      }
    } catch (error) {
      console.error('Sync error:', error);
      if (!silent) {
        showStatus('Failed to sync emails. Please try again.', 'error');
      }
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  };

  const getUnreadCount = async () => {
    const sessionId = CookieManager.get('session_id');
    if (!sessionId) return;

    try {
      const response = await fetch(`${apiBaseUrl}/gmail/unread-count?session_id=${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.count || 0);
      }
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const handleMarkAsRead = async (messageId) => {
    const sessionId = CookieManager.get('session_id');
    if (!sessionId) return;

    try {
      const response = await fetch(`${apiBaseUrl}/gmail/mark-read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message_id: messageId })
      });

      if (response.ok) {
        // Remove email from list
        const updatedEmails = emails.filter(email => email.id !== messageId);
        setEmails(updatedEmails);
        StateManager.saveEmails(updatedEmails);
        
        showStatus('✓ Email marked as read', 'success');
        await getUnreadCount();
      } else {
        showStatus('Failed to mark email as read', 'error');
      }
    } catch (error) {
      console.error('Error marking email as read:', error);
      showStatus('Failed to mark email as read', 'error');
    }
  };

  const handleReply = async (email, replyText) => {
    const sessionId = CookieManager.get('session_id');
    if (!sessionId) return false;

    try {
      showStatus('📤 Sending reply...', 'info');
      
      const response = await fetch(`${apiBaseUrl}/gmail/send-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          to: email.from,
          subject: email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`,
          message: replyText,
          thread_id: email.threadId,
          in_reply_to_message_id: email.id
        })
      });

      if (response.ok) {
        showStatus('✓ Reply sent successfully!', 'success');
        return true;
      } else {
        const data = await response.json();
        showStatus(`Failed to send reply: ${data.detail || 'Unknown error'}`, 'error');
        return false;
      }
    } catch (error) {
      console.error('Error sending reply:', error);
      showStatus('Failed to send reply', 'error');
      return false;
    }
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return '';
    const date = new Date(lastUpdate);
    return `Last updated: ${date.toLocaleString()}`;
  };

  const setupGmailWatch = async (sessionId) => {
    if (!sessionId) return;

    try {
      console.log('Setting up Gmail watch for Pub/Sub notifications...');
      const response = await fetch(`${apiBaseUrl}/gmail/watch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          topic_name: 'projects/jaano-gmail/topics/gmail-notifications'
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Gmail watch activated:', data);
        showStatus('Real-time notifications enabled!', 'success');
      } else {
        console.warn('Gmail watch setup failed:', response.status);
      }
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
          {unreadCount > 0 && (
            <p className="unread-badge">
              {unreadCount} unread email{unreadCount !== 1 ? 's' : ''}
            </p>
          )}
        </div>
        <button id="signOutBtn" className="sign-out-btn" onClick={onLogout}>
          Sign Out
        </button>
      </div>

      <div className="sync-section">
        <button
          id="syncBtn"
          className="sync-btn"
          onClick={() => syncWithGmail(false)}
          disabled={isLoading}
        >
          {isLoading ? '🔄 Syncing...' : '🔄 Refresh Emails'}
        </button>
        {lastUpdate && <p className="last-update">{formatLastUpdate()}</p>}
      </div>

      <EmailList
        emails={emails}
        onMarkAsRead={handleMarkAsRead}
        onReply={handleReply}
        isLoading={isLoading}
      />
    </div>
  );
}

export default Dashboard;
