import { api } from './client';
import type { DocumentResponse } from '../types';

export const documentsApi = {
  list: () => api.get<DocumentResponse[]>('/documents/'),

  get: (id: number) => api.get<DocumentResponse>(`/documents/${id}`),

  getText: async (id: number): Promise<string> => {
    const resp = await fetch(`/api/v1/documents/${id}/text`);
    return resp.text();
  },

  upload: (file: File, title: string, authorName?: string) => {
    const form = new FormData();
    form.append('file', file);
    form.append('title', title);
    if (authorName) form.append('author_name', authorName);
    return api.post<DocumentResponse>('/documents/', form);
  },

  update: (id: number, data: { title?: string; author_name?: string | null }) =>
    api.patch<DocumentResponse>(`/documents/${id}`, data),

  delete: (id: number) => api.delete(`/documents/${id}`),
};
