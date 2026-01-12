const EMAIL_STORAGE_KEY = 'gmail_agent_emails';
const LEAD_STORAGE_KEY = 'gmail_agent_leads';
const LAST_UPDATE_KEY = 'gmail_agent_last_update';

export const StateManager = {
  saveEmails: (emails) => {
    try {
      localStorage.setItem(EMAIL_STORAGE_KEY, JSON.stringify(emails));
      localStorage.setItem(LAST_UPDATE_KEY, new Date().toISOString());
    } catch (error) {
      console.error('Error saving emails to state:', error);
    }
  },

  loadEmails: () => {
    try {
      const stored = localStorage.getItem(EMAIL_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error loading emails from state:', error);
      return [];
    }
  },

  saveLeads: (leads) => {
    try {
      localStorage.setItem(LEAD_STORAGE_KEY, JSON.stringify(leads));
    } catch (error) {
      console.error('Error saving leads to state:', error);
    }
  },

  loadLeads: () => {
    try {
      const stored = localStorage.getItem(LEAD_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error loading leads from state:', error);
      return [];
    }
  },

  getLastUpdate: () => {
    return localStorage.getItem(LAST_UPDATE_KEY);
  },

  clearState: () => {
    localStorage.removeItem(EMAIL_STORAGE_KEY);
    localStorage.removeItem(LEAD_STORAGE_KEY);
    localStorage.removeItem(LAST_UPDATE_KEY);
  }
};
