// State Management using localStorage
export const StateManager = {
  saveEmails: (emails) => {
    try {
      localStorage.setItem('cached_emails', JSON.stringify(emails));
      localStorage.setItem('emails_last_update', new Date().toISOString());
    } catch (error) {
      console.error('Error saving emails to cache:', error);
    }
  },

  loadEmails: () => {
    try {
      const cached = localStorage.getItem('cached_emails');
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Error loading emails from cache:', error);
      return null;
    }
  },

  getLastUpdate: () => {
    return localStorage.getItem('emails_last_update');
  },

  clear: () => {
    localStorage.removeItem('cached_emails');
    localStorage.removeItem('emails_last_update');
  }
};
