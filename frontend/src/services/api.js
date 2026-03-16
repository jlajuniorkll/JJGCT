import axios from 'axios';

const api = axios.create({
   //baseURL: 'http://localhost:8000',
  // baseURL: 'http://34.61.244.240:8000',
  baseURL: '/api',
});

export const userService = {
  list: () => api.get('/usuarios/'),
  create: (data) => api.post('/usuarios/', data),
  get: (id) => api.get(`/usuarios/${id}`),
  update: (id, data) => api.put(`/usuarios/${id}`, data),
  remove: (id) => api.delete(`/usuarios/${id}`),
};

export const authService = {
  login: (email, senha) => api.post('/auth/login', { email, senha }),
};

export const vehicleService = {
  list: () => api.get('/veiculos/'),
  create: (data) => api.post('/veiculos/', data),
  get: (id) => api.get(`/veiculos/${id}`),
  update: (id, data) => api.put(`/veiculos/${id}`, data),
  remove: (id) => api.delete(`/veiculos/${id}`),
};

export const tripService = {
  list: (params) => api.get('/viagens/', { params }),
  create: (data) => api.post('/viagens/', data),
  get: (id) => api.get(`/viagens/${id}`),
  cancel: (id) => api.post(`/viagens/${id}/cancelar`),
  registerDeparture: (id) => api.post(`/viagens/${id}/registrar-saida`),
  registerArrival: (id, km_chegada) => {
    const params = {};
    if (km_chegada !== undefined && km_chegada !== null && `${km_chegada}`.trim() !== '') {
      params.km_chegada = km_chegada;
    }
    return api.post(`/viagens/${id}/registrar-chegada`, null, { params });
  },
  getReport: (id) => api.get(`/viagens/${id}/relatorio`),
};

export const expenseService = {
  create: (viagem_id, formData) => api.post('/despesas/', formData, {
    params: {
      viagem_id,
      valor: formData.get('valor'),
      forma_pagamento: formData.get('forma_pagamento'),
      descricao: formData.get('descricao'),
    },
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  get: (id) => api.get(`/despesas/${id}`),
  update: (id, formData) => api.put(`/despesas/${id}`, formData, {
    params: {
      valor: formData.get('valor'),
      forma_pagamento: formData.get('forma_pagamento'),
      descricao: formData.get('descricao'),
    },
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  remove: (id) => api.delete(`/despesas/${id}`),
};

export const activityService = {
  create: (viagem_id, data) => api.post('/atividades/', data, { params: { viagem_id } }),
  start: (id) => api.post(`/atividades/${id}/iniciar`),
  finish: (id) => api.post(`/atividades/${id}/finalizar`),
  pause: (id, data) => api.post(`/atividades/${id}/pausar`, data),
  finishPause: (pausa_id) => api.post(`/atividades/pausas/${pausa_id}/finalizar`),
};

export default api;
