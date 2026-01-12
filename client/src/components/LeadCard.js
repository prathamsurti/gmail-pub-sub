import React, { useState } from 'react';

function LeadCard({ lead, onSend, onUpdateDraft, onDismiss, showStatus }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editedSubject, setEditedSubject] = useState(lead.draft?.subject || '');
    const [editedBody, setEditedBody] = useState(lead.draft?.body || '');
    const [isSending, setIsSending] = useState(false);

    const classification = lead.classification?.toLowerCase() || 'unknown';

    const getClassificationStyle = () => {
        switch (classification) {
            case 'hot':
                return { badge: styles.hotBadge, icon: '🔥', label: 'HOT' };
            case 'warm':
                return { badge: styles.warmBadge, icon: '🟡', label: 'WARM' };
            case 'cold':
                return { badge: styles.coldBadge, icon: '🔵', label: 'COLD' };
            default:
                return { badge: styles.defaultBadge, icon: '📧', label: classification.toUpperCase() };
        }
    };

    const classStyle = getClassificationStyle();

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return date.toLocaleDateString();
    };

    const handleSend = async () => {
        setIsSending(true);
        try {
            await onSend(lead.id);
        } finally {
            setIsSending(false);
        }
    };

    const handleSaveAndSend = async () => {
        setIsSending(true);
        try {
            // First update the draft
            await onUpdateDraft(lead.id, editedSubject, editedBody);
            // Then send
            await onSend(lead.id);
            setIsEditing(false);
        } finally {
            setIsSending(false);
        }
    };

    const extractEmail = (fromField) => {
        const match = fromField?.match(/<(.+?)>/);
        return match ? match[1] : fromField;
    };

    return (
        <div style={{ ...styles.card, ...styles[`${classification}Card`] }}>
            {/* Header */}
            <div style={styles.header}>
                <div style={styles.headerLeft}>
                    <span style={{ ...styles.badge, ...classStyle.badge }}>
                        {classStyle.icon} {classStyle.label}
                    </span>
                    {lead.status === 'sent' && (
                        <span style={styles.sentBadge}>✓ Sent</span>
                    )}
                    {lead.status === 'dismissed' && (
                        <span style={styles.dismissedBadge}>Dismissed</span>
                    )}
                </div>
                <span style={styles.date}>{formatDate(lead.created_at)}</span>
            </div>

            {/* Sender & Subject */}
            <div style={styles.senderRow}>
                <strong style={styles.sender}>{lead.sender}</strong>
            </div>
            <div style={styles.subject}>{lead.subject}</div>

            {/* Snippet */}
            <p style={styles.snippet}>{lead.snippet}</p>

            {/* Confidence & Reasoning */}
            {lead.confidence && (
                <div style={styles.confidenceRow}>
                    <span style={styles.confidenceLabel}>Confidence:</span>
                    <span style={styles.confidenceValue}>{(lead.confidence * 100).toFixed(0)}%</span>
                    {lead.reasoning && (
                        <span style={styles.reasoning}> — {lead.reasoning}</span>
                    )}
                </div>
            )}

            {/* Action Buttons based on status */}
            <div style={styles.actions}>
                {lead.status === 'sent' ? (
                    // Already sent - show view option
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={styles.viewButton}
                    >
                        {isExpanded ? '▲ Hide Reply' : '▼ View Sent Reply'}
                    </button>
                ) : lead.status === 'pending_review' ? (
                    // Pending review - show action buttons
                    <>
                        {classification === 'warm' ? (
                            <button
                                onClick={() => setIsEditing(!isEditing)}
                                style={styles.editButton}
                            >
                                ✏️ {isEditing ? 'Cancel Edit' : 'Review & Edit Draft'}
                            </button>
                        ) : (
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                style={styles.viewButton}
                            >
                                {isExpanded ? '▲ Hide' : '▼ Preview Reply'}
                            </button>
                        )}
                        <button
                            onClick={handleSend}
                            disabled={isSending}
                            style={{ ...styles.sendButton, ...(classification === 'hot' ? styles.hotSendButton : {}) }}
                        >
                            {isSending ? '⏳ Sending...' : '📧 Send Reply'}
                        </button>
                        <button
                            onClick={() => onDismiss(lead.id)}
                            style={styles.dismissButton}
                        >
                            ✕ Dismiss
                        </button>
                    </>
                ) : null}
            </div>

            {/* Expanded Draft Preview (for non-editing mode) */}
            {isExpanded && !isEditing && lead.draft && (
                <div style={styles.draftPreview}>
                    <div style={styles.draftHeader}>
                        <strong>To:</strong> {extractEmail(lead.draft.to)}
                    </div>
                    <div style={styles.draftHeader}>
                        <strong>Subject:</strong> {lead.draft.subject}
                    </div>
                    <div
                        style={styles.draftBody}
                        dangerouslySetInnerHTML={{ __html: lead.draft.body }}
                    />
                </div>
            )}

            {/* Editing Mode (for WARM leads) */}
            {isEditing && lead.draft && (
                <div style={styles.editSection}>
                    <div style={styles.editRow}>
                        <label style={styles.editLabel}>Subject:</label>
                        <input
                            type="text"
                            value={editedSubject}
                            onChange={(e) => setEditedSubject(e.target.value)}
                            style={styles.editInput}
                        />
                    </div>
                    <div style={styles.editRow}>
                        <label style={styles.editLabel}>Body:</label>
                        <textarea
                            value={editedBody}
                            onChange={(e) => setEditedBody(e.target.value)}
                            rows={10}
                            style={styles.editTextarea}
                        />
                    </div>
                    <div style={styles.editActions}>
                        <button
                            onClick={handleSaveAndSend}
                            disabled={isSending}
                            style={styles.sendButton}
                        >
                            {isSending ? '⏳ Sending...' : '✅ Save & Send'}
                        </button>
                        <button
                            onClick={() => {
                                setIsEditing(false);
                                setEditedSubject(lead.draft?.subject || '');
                                setEditedBody(lead.draft?.body || '');
                            }}
                            style={styles.cancelButton}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

const styles = {
    card: {
        border: '1px solid #e0e0e0',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '12px',
        background: 'white',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        transition: 'all 0.2s'
    },
    hotCard: {
        borderLeft: '4px solid #ef4444',
        background: 'linear-gradient(to right, #fef2f2, white)'
    },
    warmCard: {
        borderLeft: '4px solid #f59e0b',
        background: 'linear-gradient(to right, #fffbeb, white)'
    },
    coldCard: {
        borderLeft: '4px solid #3b82f6',
        background: 'linear-gradient(to right, #eff6ff, white)'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '8px'
    },
    headerLeft: {
        display: 'flex',
        gap: '8px',
        alignItems: 'center'
    },
    badge: {
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '700',
        textTransform: 'uppercase'
    },
    hotBadge: {
        background: '#fee2e2',
        color: '#dc2626'
    },
    warmBadge: {
        background: '#fef3c7',
        color: '#d97706'
    },
    coldBadge: {
        background: '#dbeafe',
        color: '#2563eb'
    },
    defaultBadge: {
        background: '#f3f4f6',
        color: '#6b7280'
    },
    sentBadge: {
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: '600',
        background: '#dcfce7',
        color: '#16a34a'
    },
    dismissedBadge: {
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: '600',
        background: '#f3f4f6',
        color: '#9ca3af'
    },
    date: {
        color: '#9ca3af',
        fontSize: '13px'
    },
    senderRow: {
        marginBottom: '4px'
    },
    sender: {
        fontSize: '15px',
        color: '#111827'
    },
    subject: {
        fontSize: '16px',
        fontWeight: '600',
        color: '#374151',
        marginBottom: '8px'
    },
    snippet: {
        color: '#6b7280',
        fontSize: '14px',
        lineHeight: '1.5',
        margin: '0 0 12px 0'
    },
    confidenceRow: {
        fontSize: '12px',
        color: '#6b7280',
        marginBottom: '12px'
    },
    confidenceLabel: {
        fontWeight: '500'
    },
    confidenceValue: {
        fontWeight: '600',
        color: '#374151'
    },
    reasoning: {
        fontStyle: 'italic'
    },
    actions: {
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap'
    },
    viewButton: {
        padding: '8px 16px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        borderRadius: '6px',
        background: 'white',
        cursor: 'pointer',
        fontWeight: '500'
    },
    editButton: {
        padding: '8px 16px',
        fontSize: '13px',
        border: '1px solid #f59e0b',
        borderRadius: '6px',
        background: '#fffbeb',
        color: '#d97706',
        cursor: 'pointer',
        fontWeight: '500'
    },
    sendButton: {
        padding: '8px 16px',
        fontSize: '13px',
        border: 'none',
        borderRadius: '6px',
        background: '#10b981',
        color: 'white',
        cursor: 'pointer',
        fontWeight: '600'
    },
    hotSendButton: {
        background: '#ef4444'
    },
    dismissButton: {
        padding: '8px 16px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        borderRadius: '6px',
        background: 'white',
        color: '#6b7280',
        cursor: 'pointer'
    },
    cancelButton: {
        padding: '8px 16px',
        fontSize: '13px',
        border: '1px solid #e5e7eb',
        borderRadius: '6px',
        background: 'white',
        cursor: 'pointer'
    },
    draftPreview: {
        marginTop: '16px',
        padding: '16px',
        background: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
    },
    draftHeader: {
        fontSize: '13px',
        marginBottom: '8px',
        color: '#374151'
    },
    draftBody: {
        fontSize: '14px',
        lineHeight: '1.6',
        color: '#4b5563',
        marginTop: '12px'
    },
    editSection: {
        marginTop: '16px',
        padding: '16px',
        background: '#fffbeb',
        borderRadius: '8px',
        border: '1px solid #fcd34d'
    },
    editRow: {
        marginBottom: '12px'
    },
    editLabel: {
        display: 'block',
        fontSize: '13px',
        fontWeight: '600',
        marginBottom: '4px',
        color: '#374151'
    },
    editInput: {
        width: '100%',
        padding: '10px',
        fontSize: '14px',
        border: '1px solid #d1d5db',
        borderRadius: '6px',
        boxSizing: 'border-box'
    },
    editTextarea: {
        width: '100%',
        padding: '10px',
        fontSize: '14px',
        border: '1px solid #d1d5db',
        borderRadius: '6px',
        boxSizing: 'border-box',
        fontFamily: 'inherit',
        resize: 'vertical'
    },
    editActions: {
        display: 'flex',
        gap: '8px'
    }
};

export default LeadCard;
