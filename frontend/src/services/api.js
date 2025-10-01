import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Lab Assistants API
export const getLabAssistants = () => {
  return api.get('/lab-assistants/');
};

export const getLabAssistant = (id) => {
  return api.get(`/lab-assistants/${id}/`);
};

export const getLabAssistantAvailability = (id) => {
  return api.get(`/lab-assistants/${id}/availability/`);
};

// Availability API
export const getAvailability = (params = {}) => {
  return api.get('/availability/', { params });
};

export const createAvailability = (data) => {
  return api.post('/availability/', data);
};

export const updateAvailability = (id, data) => {
  return api.put(`/availability/${id}/`, data);
};

export const deleteAvailability = (id) => {
  return api.delete(`/availability/${id}/`);
};

// Export default object with all methods
export default {
  getLabAssistants,
  getLabAssistant,
  getLabAssistantAvailability,
  getAvailability,
  createAvailability,
  updateAvailability,
  deleteAvailability,
};