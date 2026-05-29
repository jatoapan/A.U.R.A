import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejo de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const siniestrosAPI = {
  // Health check
  health: () => api.get('/health'),

  // Listado
  list: (params = {}) => api.get('/siniestros', { params }),

  // Detalle
  get: (id) => api.get(`/siniestros/${id}`),

  // Score
  score: (id) => api.post(`/siniestros/${id}/score`),
  scoreAll: () => api.post('/siniestros/score-all'),

  // Chat
  chat: (id, messages) =>
    api.post(`/siniestros/${id}/chat`, { messages }),
};

export default api;
