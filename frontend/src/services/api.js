const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = {
  fetchUsers: async ({ page = 1, pageSize = 10, email = '' }) => {
    const response = await fetch(
      `${API_BASE_URL}/auth/api/users?page=${page}&per_page=${pageSize}&email=${email}`
    );
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
  },

  updateUser: async (userId, data) => {
    const response = await fetch(`${API_BASE_URL}/auth/api/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update user');
    return response.json();
  },

  activateUser: async (userId) => {
    const response = await fetch(`${API_BASE_URL}/auth/api/users/${userId}/activate`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to activate user');
    return response.json();
  },

  deactivateUser: async (userId) => {
    const response = await fetch(`${API_BASE_URL}/auth/api/users/${userId}/deactivate`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to deactivate user');
    return response.json();
  },

  resetPassword: async (userId, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/api/users/${userId}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    if (!response.ok) throw new Error('Failed to reset password');
    return response.json();
  },

  async login({ email, password, remember = true }) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password, remember }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }

    return response.json();
  },

  async logout() {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Logout failed');
    }
  },

  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  }
};