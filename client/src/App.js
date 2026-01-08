import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { CookieManager } from './utils/cookieManager';
import { StateManager } from './utils/stateManager';

// Backend API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  useEffect(() => {
    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.has('session_id')) {
      handleOAuthCallback(urlParams);
    } else if (urlParams.has('error')) {
      showStatus('Authentication failed. Please try again.', 'error');
      window.history.replaceState({}, document.title, '/');
    } else {
      // Check existing session
      checkExistingSession();
    }
  }, []);

  const handleOAuthCallback = (urlParams) => {
    const sessionId = urlParams.get('session_id');
    const accessToken = urlParams.get('access_token');
    const refreshToken = urlParams.get('refresh_token');
    const userName = urlParams.get('user_name');
    const userEmail = urlParams.get('user_email');

    // Store in cookies
    CookieManager.set('session_id', sessionId, 7);
    if (accessToken) CookieManager.set('google_access_token', accessToken, 7);
    if (refreshToken) CookieManager.set('google_refresh_token', refreshToken, 30);
    if (userName) CookieManager.set('user_name', decodeURIComponent(userName), 7);
    if (userEmail) CookieManager.set('user_email', decodeURIComponent(userEmail), 7);

    // Clean URL
    window.history.replaceState({}, document.title, '/');

    // Set authenticated state
    setUserInfo({
      name: decodeURIComponent(userName),
      email: decodeURIComponent(userEmail)
    });
    setIsAuthenticated(true);
    showStatus('Successfully signed in with Google!', 'success');
  };

  const checkExistingSession = () => {
    const sessionId = CookieManager.get('session_id');
    const userName = CookieManager.get('user_name');
    const userEmail = CookieManager.get('user_email');

    if (sessionId && userName && userEmail) {
      setUserInfo({ name: userName, email: userEmail });
      setIsAuthenticated(true);
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`);
      const data = await response.json();

      if (data.authorization_url) {
        sessionStorage.setItem('oauth_state', data.state);
        window.location.href = data.authorization_url;
      } else {
        throw new Error('Failed to get authorization URL');
      }
    } catch (error) {
      console.error('Sign-in error:', error);
      showStatus('Failed to initiate sign-in. Please try again.', 'error');
    }
  };

  const handleLogout = async () => {
    const sessionId = CookieManager.get('session_id');

    console.log('Logging out...', { sessionId });

    // Clear cached state
    StateManager.clear();

    // Call backend logout
    if (sessionId) {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/logout?session_id=${sessionId}`, {
          method: 'POST'
        });
        console.log('Logout response:', response.status);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    // Clear all cookies
    CookieManager.delete('session_id');
    CookieManager.delete('google_access_token');
    CookieManager.delete('google_refresh_token');
    CookieManager.delete('user_name');
    CookieManager.delete('user_email');

    setIsAuthenticated(false);
    setUserInfo(null);
    showStatus('Successfully signed out.', 'info');

    console.log('Logout complete');
  };

  const showStatus = (message, type = 'info') => {
    setStatusMessage({ message, type });
    setTimeout(() => setStatusMessage(null), 5000);
  };

  return (
    <div className="App">
      <div className="container">
        <h1>📧 Gmail Integration</h1>
        <p className="subtitle">Sign in with Google to sync your emails</p>

        {!isAuthenticated ? (
          <Login onLogin={handleLogin} />
        ) : (
          <Dashboard
            userInfo={userInfo}
            onLogout={handleLogout}
            showStatus={showStatus}
            apiBaseUrl={API_BASE_URL}
          />
        )}

        {statusMessage && (
          <div className={`status-message status-${statusMessage.type}`}>
            {statusMessage.message}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
