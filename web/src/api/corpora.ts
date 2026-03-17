import { api } from './client';
import type { CorpusResponse, DocumentResponse, SampleCorpusImportResponse, SampleCorpusInfo } from '../types';

export const corporaApi = {
  list: () => api.get<CorpusResponse[]>('/corpora/'),

  get: (id: number) => api.get<CorpusResponse>(`/corpora/${id}`),

  create: (name: string, description?: string) =>
    api.post<CorpusResponse>('/corpora/', { name, description: description || '' }),

  update: (id: number, data: { name?: string; description?: string }) =>
    api.patch<CorpusResponse>(`/corpora/${id}`, data),

  delete: (id: number) => api.delete(`/corpora/${id}`),

  listDocuments: (id: number) =>
    api.get<DocumentResponse[]>(`/corpora/${id}/documents`),

  addDocuments: (id: number, documentIds: number[]) =>
    api.post<CorpusResponse>(`/corpora/${id}/documents`, { document_ids: documentIds }),

  removeDocuments: (id: number, documentIds: number[]) =>
    fetch(`/api/v1/corpora/${id}/documents`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids: documentIds }),
    }).then((r) => r.json()) as Promise<CorpusResponse>,
};

export const sampleCorporaApi = {
  list: () => api.get<SampleCorpusInfo[]>('/sample-corpora/'),

  import: (corpusId: string) =>
    api.post<SampleCorpusImportResponse>(`/sample-corpora/${corpusId}/import`),
};
