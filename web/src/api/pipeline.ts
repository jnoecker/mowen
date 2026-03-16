import { api } from './client';
import type { ComponentInfo } from '../types';

export const pipelineApi = {
  getCanonicizers: () => api.get<ComponentInfo[]>('/pipeline/canonicizers'),
  getEventDrivers: () => api.get<ComponentInfo[]>('/pipeline/event-drivers'),
  getEventCullers: () => api.get<ComponentInfo[]>('/pipeline/event-cullers'),
  getDistanceFunctions: () => api.get<ComponentInfo[]>('/pipeline/distance-functions'),
  getAnalysisMethods: () => api.get<ComponentInfo[]>('/pipeline/analysis-methods'),
};
