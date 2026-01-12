import React, { useState, useEffect } from 'react';
import LeadCard from './LeadCard';
import { CookieManager } from '../utils/cookieManager';

function LeadsDashboard({ showStatus, apiBaseUrl, lastUpdate, newLead }) {
    const [leads, setLeads] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [filter, setFilter] = useState('all'); // all, hot, warm, cold, pending, sent

    // Fetch leads when lastUpdate changes (manual sync or initial load)
    useEffect(() => {
        fetchLeads();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [lastUpdate]);

    // Handle new lead push update
    useEffect(() => {
        if (newLead) {
            setLeads(prevLeads => {
                // Prevent duplicates
                if (prevLeads.some(l => l.id === newLead.id)) {
                    return prevLeads;
                }
                return [newLead, ...prevLeads];
            });
        }
    }, [newLead]);

    const fetchLeads = async () => {
        const sessionId = CookieManager.get('session_id');
        if (!sessionId) {
            // Only show error if we expected a session (avoid flash on login screen)
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch(`${apiBaseUrl}/leads?session_id=${sessionId}`);
            if (response.ok) {
                const data = await response.json();
                setLeads(data.leads || []);
            } else {
                showStatus('Failed to fetch leads', 'error');
            }
        } catch (error) {
            console.error('Error fetching leads:', error);
            showStatus('Failed to fetch leads', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = async (leadId) => {
        const sessionId = CookieManager.get('session_id');
        if (!sessionId) return;

        try {
            const response = await fetch(`${apiBaseUrl}/leads/${leadId}/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });

            if (response.ok) {
                const data = await response.json();
                // Update lead in local state
                setLeads(prevLeads =>
                    prevLeads.map(lead =>
                        lead.id === leadId ? data.lead : lead
                    )
                );
                showStatus('✓ Reply sent successfully!', 'success');
            } else {
                const error = await response.json();
                showStatus(`Failed to send: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error sending lead:', error);
            showStatus('Failed to send reply', 'error');
        }
    };

    const handleUpdateDraft = async (leadId, subject, body) => {
        const sessionId = CookieManager.get('session_id');
        if (!sessionId) return;

        try {
            const response = await fetch(`${apiBaseUrl}/leads/${leadId}/draft`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, subject, body })
            });

            if (response.ok) {
                const data = await response.json();
                setLeads(prevLeads =>
                    prevLeads.map(lead =>
                        lead.id === leadId ? data.lead : lead
                    )
                );
            }
        } catch (error) {
            console.error('Error updating draft:', error);
        }
    };

    const handleDismiss = async (leadId) => {
        const sessionId = CookieManager.get('session_id');
        if (!sessionId) return;

        try {
            const response = await fetch(`${apiBaseUrl}/leads/${leadId}/dismiss?session_id=${sessionId}`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                setLeads(prevLeads =>
                    prevLeads.map(lead =>
                        lead.id === leadId ? data.lead : lead
                    )
                );
                showStatus('Lead dismissed', 'info');
            }
        } catch (error) {
            console.error('Error dismissing lead:', error);
        }
    };

    // Filter leads
    const filteredLeads = leads.filter(lead => {
        if (filter === 'all') return lead.status !== 'dismissed';
        if (filter === 'pending') return lead.status === 'pending_review';
        if (filter === 'sent') return lead.status === 'sent';
        if (filter === 'hot') return lead.classification?.toLowerCase() === 'hot';
        if (filter === 'warm') return lead.classification?.toLowerCase() === 'warm';
        if (filter === 'cold') return lead.classification?.toLowerCase() === 'cold';
        return true;
    });

    // Count by classification
    const counts = {
        all: leads.filter(l => l.status !== 'dismissed').length,
        pending: leads.filter(l => l.status === 'pending_review').length,
        sent: leads.filter(l => l.status === 'sent').length,
        hot: leads.filter(l => l.classification?.toLowerCase() === 'hot').length,
        warm: leads.filter(l => l.classification?.toLowerCase() === 'warm').length,
        cold: leads.filter(l => l.classification?.toLowerCase() === 'cold').length
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h2 style={styles.title}>📊 Leads Dashboard</h2>
                <button
                    onClick={fetchLeads}
                    disabled={isLoading}
                    style={styles.refreshButton}
                >
                    {isLoading ? '🔄 Loading...' : '🔄 Refresh'}
                </button>
            </div>

            {/* Filter Tabs */}
            <div style={styles.filters}>
                <button
                    onClick={() => setFilter('all')}
                    style={{ ...styles.filterTab, ...(filter === 'all' ? styles.activeFilter : {}) }}
                >
                    All ({counts.all})
                </button>
                <button
                    onClick={() => setFilter('pending')}
                    style={{ ...styles.filterTab, ...(filter === 'pending' ? styles.activeFilter : {}) }}
                >
                    ⏳ Pending ({counts.pending})
                </button>
                <button
                    onClick={() => setFilter('sent')}
                    style={{ ...styles.filterTab, ...(filter === 'sent' ? styles.activeFilter : {}) }}
                >
                    ✓ Sent ({counts.sent})
                </button>
                <span style={styles.divider}>|</span>
                <button
                    onClick={() => setFilter('hot')}
                    style={{ ...styles.filterTab, ...(filter === 'hot' ? styles.activeFilter : {}), ...styles.hotFilter }}
                >
                    🔥 Hot ({counts.hot})
                </button>
                <button
                    onClick={() => setFilter('warm')}
                    style={{ ...styles.filterTab, ...(filter === 'warm' ? styles.activeFilter : {}), ...styles.warmFilter }}
                >
                    🟡 Warm ({counts.warm})
                </button>
                <button
                    onClick={() => setFilter('cold')}
                    style={{ ...styles.filterTab, ...(filter === 'cold' ? styles.activeFilter : {}), ...styles.coldFilter }}
                >
                    🔵 Cold ({counts.cold})
                </button>
            </div>

            {/* Leads List */}
            <div style={styles.leadsList}>
                {isLoading && leads.length === 0 ? (
                    <div style={styles.emptyState}>
                        <p>🔄 Loading leads...</p>
                    </div>
                ) : filteredLeads.length === 0 ? (
                    <div style={styles.emptyState}>
                        <p>📭 No leads found</p>
                        <p style={styles.emptySubtext}>
                            {filter === 'all'
                                ? 'New emails will be analyzed and leads will appear here'
                                : 'No leads match the selected filter'}
                        </p>
                    </div>
                ) : (
                    filteredLeads.map(lead => (
                        <LeadCard
                            key={lead.id}
                            lead={lead}
                            onSend={handleSend}
                            onUpdateDraft={handleUpdateDraft}
                            onDismiss={handleDismiss}
                            showStatus={showStatus}
                        />
                    ))
                )}
            </div>

            {/* Info */}
            <div style={styles.info}>
                <p><strong>💡 How it works:</strong></p>
                <ul style={styles.infoList}>
                    <li>🔥 <strong>Hot Leads</strong> are auto-sent immediately</li>
                    <li>🟡 <strong>Warm Leads</strong> need your review - edit the draft before sending</li>
                    <li>🔵 <strong>Cold Leads</strong> get a company info template - review and send</li>
                </ul>
            </div>
        </div>
    );
}

const styles = {
    container: {
        padding: '20px 0'
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
    },
    title: {
        fontSize: '24px',
        fontWeight: '700',
        color: '#111827',
        margin: 0
    },
    refreshButton: {
        padding: '10px 20px',
        fontSize: '14px',
        fontWeight: '600',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        background: 'white',
        cursor: 'pointer'
    },
    filters: {
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        flexWrap: 'wrap',
        alignItems: 'center'
    },
    filterTab: {
        padding: '8px 16px',
        fontSize: '13px',
        fontWeight: '500',
        border: '1px solid #e5e7eb',
        borderRadius: '20px',
        background: 'white',
        cursor: 'pointer',
        transition: 'all 0.2s'
    },
    activeFilter: {
        background: '#667eea',
        color: 'white',
        borderColor: '#667eea'
    },
    divider: {
        color: '#d1d5db',
        margin: '0 4px'
    },
    hotFilter: {},
    warmFilter: {},
    coldFilter: {},
    leadsList: {
        minHeight: '200px'
    },
    emptyState: {
        textAlign: 'center',
        padding: '60px 20px',
        color: '#6b7280'
    },
    emptySubtext: {
        fontSize: '14px',
        color: '#9ca3af',
        marginTop: '8px'
    },
    info: {
        marginTop: '30px',
        padding: '16px',
        background: '#f0f9ff',
        borderRadius: '8px',
        fontSize: '14px',
        color: '#0369a1'
    },
    infoList: {
        margin: '8px 0 0 0',
        paddingLeft: '20px'
    }
};

export default LeadsDashboard;
