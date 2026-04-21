import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// CONFIG APIs
export const configApi = {
  // Repository management
  getAllRepos: (params = {}) => api.get('/api/config/repos', { params }), // ← ADDED
  enrollRepo: (data) => api.post('/api/config/repos', data),
  getRepo: (repoId) => api.get(`/api/config/repos/${repoId}`),
  updateRepo: (repoId, data) => api.patch(`/api/config/repos/${repoId}`, data),
  
  // Developer management
  addDeveloper: (repoId, data) => api.post(`/api/config/repos/${repoId}/developers`, data),
  updateDeveloper: (repoId, githubLogin, data) => 
    api.patch(`/api/config/repos/${repoId}/developers/${githubLogin}`, data),
  deleteDeveloper: (repoId, githubLogin) => 
    api.delete(`/api/config/repos/${repoId}/developers/${githubLogin}`),
};

// OBSERVABILITY APIs
export const observabilityApi = {
  getTriageHistory: (repoId, params = {}) => 
    api.get(`/api/triage/${repoId}`, { params }),
  getWorkload: (repoId) => api.get(`/api/workload/${repoId}`),
  getProductivity: (repoId, window = '30d') => 
    api.get(`/api/productivity/${repoId}`, { params: { window } }),
  getIssues: (repoId, params = {}) => 
    api.get(`/api/issues/${repoId}`, { params }),
};



export const healthCheck = () => api.get('/health');

export default api;