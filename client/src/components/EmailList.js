import React from 'react';
import EmailItem from './EmailItem';

function EmailList({ emails, onMarkAsRead, onReply, isLoading }) {
  if (isLoading && emails.length === 0) {
    return (
      <div id="emailsSection" className="emails-section">
        <div className="loading">Loading emails...</div>
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div id="emailsSection" className="emails-section">
        <div className="no-emails">
          <p>📭 No unread emails</p>
          <p className="subtitle">You're all caught up!</p>
        </div>
      </div>
    );
  }

  return (
    <div id="emailsSection" className="emails-section">
      <h3>Unread Emails ({emails.length})</h3>
      <div id="emailsList" className="emails-list">
        {emails.map((email) => (
          <EmailItem
            key={email.id}
            email={email}
            onMarkAsRead={onMarkAsRead}
            onReply={onReply}
          />
        ))}
      </div>
    </div>
  );
}

export default EmailList;
