import { api } from './client';
import type { ExperimentCreate, ExperimentResponse, ExperimentResultResponse } from '../types';

export const experimentsApi = {
  list: () => api.get<ExperimentResponse[]>('/experiments/'),

  get: (id: number) => api.get<ExperimentResponse>(`/experiments/${id}`),

  create: (data: ExperimentCreate) =>
    api.post<ExperimentResponse>('/experiments/', data),

  delete: (id: number) => api.delete(`/experiments/${id}`),

  getResults: (id: number) =>
    api.get<ExperimentResultResponse[]>(`/experiments/${id}/results`),
};
