import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadResume = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/candidates/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress && onProgress(percentCompleted);
    },
  });

  return response.data;
};

export const getCandidates = async () => {
  const response = await api.get('/candidates');
  return response.data.candidates;
};

export const getCandidate = async (id) => {
  const response = await api.get(`/candidates/${id}`);
  return response.data;
};

export const requestDocuments = async (id) => {
  const response = await api.post(`/candidates/${id}/request-documents`);
  return response.data;
};

export const submitDocuments = async (id, panFile, aadhaarFile) => {
  const formData = new FormData();
  if (panFile) formData.append('pan', panFile);
  if (aadhaarFile) formData.append('aadhaar', aadhaarFile);

  const response = await api.post(`/candidates/${id}/submit-documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};
