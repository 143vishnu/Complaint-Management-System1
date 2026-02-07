/**
 * Feature Utilities and Helpers
 * Handles tags, search, export, comments, etc.
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

/**
 * Tags Management
 */
export const tagsAPI = {
  getTags: async (complaintId, token) => {
    const response = await axios.get(
      `${API_URL}/api/features/complaints/${complaintId}/tags`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  addTags: async (complaintId, tags, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/complaints/${complaintId}/tags`,
      { tags },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  removeTag: async (complaintId, tag, token) => {
    const response = await axios.delete(
      `${API_URL}/api/features/complaints/${complaintId}/tags/${tag}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  getPopularTags: async (token) => {
    const response = await axios.get(
      `${API_URL}/api/features/tags/popular`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Admin Notes (Internal, not visible to users)
 */
export const adminNotesAPI = {
  getNotes: async (complaintId, token) => {
    const response = await axios.get(
      `${API_URL}/api/features/complaints/${complaintId}/notes`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  addNote: async (complaintId, noteText, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/complaints/${complaintId}/notes`,
      { note_text: noteText },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Comments (Public discussion thread)
 */
export const commentsAPI = {
  getComments: async (complaintId, token) => {
    const response = await axios.get(
      `${API_URL}/api/features/complaints/${complaintId}/comments`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  addComment: async (complaintId, commentText, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/complaints/${complaintId}/comments`,
      { comment_text: commentText },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Canned Responses (Admin templates)
 */
export const cannedResponsesAPI = {
  getResponses: async (category, token) => {
    const url = category
      ? `${API_URL}/api/features/canned-responses?category=${category}`
      : `${API_URL}/api/features/canned-responses`;
    const response = await axios.get(url, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  createResponse: async (title, body, category, isGlobal, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/canned-responses`,
      { title, body, category, is_global: isGlobal },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  deleteResponse: async (responseId, token) => {
    const response = await axios.delete(
      `${API_URL}/api/features/canned-responses/${responseId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Complaint Templates (User quick submit)
 */
export const templatesAPI = {
  getTemplates: async (token) => {
    const response = await axios.get(
      `${API_URL}/api/features/templates`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },

  createTemplate: async (title, descriptionTemplate, category, suggestedPriority, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/templates`,
      {
        title,
        description_template: descriptionTemplate,
        category,
        suggested_priority: suggestedPriority
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Search
 */
export const searchAPI = {
  search: async (queryText, filters = {}, page = 1, token) => {
    const params = new URLSearchParams({
      q: queryText,
      page,
      ...filters
    });
    const response = await axios.get(
      `${API_URL}/api/features/search?${params}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Export
 */
export const exportAPI = {
  exportCSV: async (token) => {
    try {
      const response = await axios.get(
        `${API_URL}/api/features/export/complaints`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `complaints_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentURL.removeChild(link);
    } catch (error) {
      throw new Error('Failed to export complaints');
    }
  }
};

/**
 * Assignment
 */
export const assignmentAPI = {
  assignComplaint: async (complaintId, adminId, token) => {
    const response = await axios.post(
      `${API_URL}/api/features/complaints/${complaintId}/assign`,
      { admin_id: adminId },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * SLA Tracking
 */
export const slaAPI = {
  getSLATracking: async (complaintId, token) => {
    const response = await axios.get(
      `${API_URL}/api/features/complaints/${complaintId}/sla`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Escalation
 */
export const escalationAPI = {
  escalateStaleComplaints: async (token) => {
    const response = await axios.post(
      `${API_URL}/api/features/escalate-stale`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Anonymous Toggle
 */
export const anonymousAPI = {
  toggleAnonymous: async (complaintId, token) => {
    const response = await axios.put(
      `${API_URL}/api/features/complaints/${complaintId}/toggle-anonymous`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  }
};

/**
 * Utility: Format date and time
 */
export const formatDateTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Utility: Get time ago
 */
export const getTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  
  return date.toLocaleDateString();
};

/**
 * Utility: Validate email
 */
export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

/**
 * Utility: Debounce function
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};
