import React, { useState } from 'react';

function EmailItem({ email, onMarkAsRead, onReply }) {
  const [showReplyBox, setShowReplyBox] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isSending, setIsSending] = useState(false);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const truncateSnippet = (snippet, maxLength = 150) => {
    if (!snippet) return '';
    return snippet.length > maxLength ? `${snippet.substring(0, maxLength)}...` : snippet;
  };

  const handleSendReply = async () => {
    if (!replyText.trim()) return;

    setIsSending(true);
    const success = await onReply(email, replyText);
    setIsSending(false);

    if (success) {
      setReplyText('');
      setShowReplyBox(false);
    }
  };

  const extractEmail = (fromField) => {
    const match = fromField.match(/<(.+?)>/);
    return match ? match[1] : fromField;
  };

  return (
    <div className="email-item">
      <div className="email-header">
        <strong className="email-from">{email.from}</strong>
        <span className="email-date">{formatDate(email.date)}</span>
      </div>
      <div className="email-subject">{email.subject}</div>
      <div className="email-snippet">{truncateSnippet(email.snippet)}</div>

      <div className="email-actions">
        <button
          className="reply-btn"
          onClick={() => setShowReplyBox(!showReplyBox)}
        >
          ↩️ Reply
        </button>
        <button
          className="mark-read-btn"
          onClick={() => onMarkAsRead(email.id)}
        >
          ✓ Mark as Read
        </button>
      </div>

      {showReplyBox && (
        <div className="reply-box">
          <div className="reply-header">
            <strong>Reply to:</strong> {extractEmail(email.from)}
          </div>
          <textarea
            className="reply-textarea"
            placeholder="Type your reply..."
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            rows="6"
          />
          <div className="reply-actions">
            <button
              className="send-reply-btn"
              onClick={handleSendReply}
              disabled={isSending || !replyText.trim()}
            >
              {isSending ? 'Sending...' : '📧 Send Reply'}
            </button>
            <button
              className="cancel-reply-btn"
              onClick={() => {
                setShowReplyBox(false);
                setReplyText('');
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmailItem;
