import { useState, type FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { corporaApi, sampleCorporaApi } from '../api/corpora';
import { documentsApi } from '../api/documents';
import type { CorpusResponse, DocumentResponse, SampleCorpusInfo } from '../types';

// ---------------------------------------------------------------------------
// Shared styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border)',
  borderRadius: '8px',
  padding: '1.25rem',
  marginBottom: '1rem',
};

const inputStyle: React.CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  padding: '0.4rem 0.6rem',
  fontSize: '0.85rem',
  width: '100%',
};

// ---------------------------------------------------------------------------
// Document assignment panel (shown when a corpus card is expanded)
// ---------------------------------------------------------------------------

function DocumentAssignment({
  corpus,
  allDocuments,
}: {
  corpus: CorpusResponse;
  allDocuments: DocumentResponse[];
}) {
  const queryClient = useQueryClient();
  const [selectedDocId, setSelectedDocId] = useState<number | ''>('');

  const {
    data: corpusDocuments = [],
    isLoading,
  } = useQuery({
    queryKey: ['corpora', corpus.id, 'documents'],
    queryFn: () => corporaApi.listDocuments(corpus.id),
  });

  const addMutation = useMutation({
    mutationFn: (docId: number) => corporaApi.addDocuments(corpus.id, [docId]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corpora', corpus.id, 'documents'] });
      queryClient.invalidateQueries({ queryKey: ['corpora'] });
      setSelectedDocId('');
    },
  });

  const removeMutation = useMutation({
    mutationFn: (docId: number) => corporaApi.removeDocuments(corpus.id, [docId]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corpora', corpus.id, 'documents'] });
      queryClient.invalidateQueries({ queryKey: ['corpora'] });
    },
  });

  const corpusDocIds = new Set(corpusDocuments.map((d) => d.id));
  const availableDocuments = allDocuments.filter((d) => !corpusDocIds.has(d.id));

  const handleAdd = () => {
    if (selectedDocId === '') return;
    addMutation.mutate(selectedDocId);
  };

  return (
    <div
      style={{
        marginTop: '0.75rem',
        paddingTop: '0.75rem',
        borderTop: '1px solid var(--border)',
      }}
    >
      <h3 style={{ marginBottom: '0.5rem', fontSize: '0.95rem' }}>Documents in Corpus</h3>

      {isLoading && <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading...</p>}

      {!isLoading && corpusDocuments.length === 0 && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          No documents assigned yet.
        </p>
      )}

      {!isLoading && corpusDocuments.length > 0 && (
        <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 0.75rem 0' }}>
          {corpusDocuments.map((doc) => (
            <li
              key={doc.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.35rem 0.5rem',
                borderRadius: 'var(--radius)',
                marginBottom: '0.25rem',
                background: 'var(--bg-elevated)',
                fontSize: '0.85rem',
              }}
            >
              <span>
                <strong>{doc.title}</strong>
                {doc.author_name && (
                  <span style={{ color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                    by {doc.author_name}
                  </span>
                )}
              </span>
              <button
                style={{
                  padding: '0.2rem 0.5rem',
                  fontSize: '0.8rem',
                  color: 'var(--danger)',
                  borderColor: 'var(--danger)',
                }}
                onClick={() => removeMutation.mutate(doc.id)}
                disabled={removeMutation.isPending}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Add-document selector */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <select
          value={selectedDocId}
          onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : '')}
          style={{ ...inputStyle, flex: '1 1 auto' }}
          disabled={availableDocuments.length === 0}
        >
          <option value="">
            {availableDocuments.length === 0
              ? 'No documents available to add'
              : 'Select a document to add...'}
          </option>
          {availableDocuments.map((doc) => (
            <option key={doc.id} value={doc.id}>
              {doc.title}
              {doc.author_name ? ` (${doc.author_name})` : ''}
            </option>
          ))}
        </select>
        <button
          className="primary"
          style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
          onClick={handleAdd}
          disabled={selectedDocId === '' || addMutation.isPending}
        >
          Add
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Single corpus card
// ---------------------------------------------------------------------------

function CorpusCard({
  corpus,
  allDocuments,
}: {
  corpus: CorpusResponse;
  allDocuments: DocumentResponse[];
}) {
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(corpus.name);
  const [description, setDescription] = useState(corpus.description);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const updateMutation = useMutation({
    mutationFn: (data: { name?: string; description?: string }) =>
      corporaApi.update(corpus.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corpora'] });
      setEditing(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => corporaApi.delete(corpus.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['corpora'] }),
  });

  const handleSave = () => {
    updateMutation.mutate({ name, description });
  };

  const handleCancel = () => {
    setName(corpus.name);
    setDescription(corpus.description);
    setEditing(false);
  };

  const handleDelete = () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    deleteMutation.mutate();
    setConfirmDelete(false);
  };

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          {editing ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div>
                <label>Name</label>
                <input
                  style={inputStyle}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div>
                <label>Description</label>
                <input
                  style={inputStyle}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                />
              </div>
            </div>
          ) : (
            <>
              <h2 style={{ marginBottom: '0.25rem' }}>{corpus.name}</h2>
              {corpus.description && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                  {corpus.description}
                </p>
              )}
            </>
          )}

          <div
            style={{
              display: 'flex',
              gap: '1.25rem',
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              marginTop: '0.35rem',
            }}
          >
            <span>{corpus.document_count} document{corpus.document_count !== 1 ? 's' : ''}</span>
            <span>Created {new Date(corpus.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0, marginLeft: '1rem' }}>
          {editing ? (
            <>
              <button className="primary" onClick={handleSave} disabled={!name.trim()}>
                Save
              </button>
              <button onClick={handleCancel}>Cancel</button>
            </>
          ) : (
            <>
              <button onClick={() => setExpanded(!expanded)}>
                {expanded ? 'Collapse' : 'Expand'}
              </button>
              <button onClick={() => setEditing(true)}>Edit</button>
              <button
                style={
                  confirmDelete
                    ? { background: 'var(--danger)', borderColor: 'var(--danger)', color: '#fff' }
                    : {}
                }
                onClick={handleDelete}
                onBlur={() => setConfirmDelete(false)}
              >
                {confirmDelete ? 'Confirm' : 'Delete'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Expanded document assignment */}
      {expanded && <DocumentAssignment corpus={corpus} allDocuments={allDocuments} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sample corpus importer
// ---------------------------------------------------------------------------

function SampleCorpusImporter() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState('');

  const { data: sampleCorpora = [] } = useQuery({
    queryKey: ['sample-corpora'],
    queryFn: sampleCorporaApi.list,
  });

  const importMutation = useMutation({
    mutationFn: (corpusId: string) => sampleCorporaApi.import(corpusId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corpora'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setSelectedId('');
    },
  });

  const selected = sampleCorpora.find((c: SampleCorpusInfo) => c.id === selectedId);

  return (
    <div style={cardStyle}>
      <h2 style={{ marginBottom: '0.75rem' }}>Import Sample Corpus</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
        Import a standard AAAC benchmark problem set with pre-labeled training and unknown documents.
      </p>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', flexDirection: 'column', flex: '1 1 300px' }}>
          <label>Sample Corpus</label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            style={inputStyle}
            disabled={sampleCorpora.length === 0 || importMutation.isPending}
          >
            <option value="">
              {sampleCorpora.length === 0 ? 'Loading...' : 'Select a sample corpus...'}
            </option>
            {sampleCorpora.map((c: SampleCorpusInfo) => (
              <option key={c.id} value={c.id}>
                {c.name} — {c.num_authors} authors, {c.num_known + c.num_unknown} docs
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            className="primary"
            onClick={() => importMutation.mutate(selectedId)}
            disabled={!selectedId || importMutation.isPending}
          >
            {importMutation.isPending ? 'Importing...' : 'Import'}
          </button>
        </div>
      </div>

      {selected && !importMutation.isPending && !importMutation.isSuccess && (
        <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {selected.description}
        </p>
      )}

      {importMutation.isSuccess && (
        <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--success, #4caf50)' }}>
          Imported successfully! Created "{importMutation.data.known_corpus.name}" ({importMutation.data.known_corpus.document_count} docs) and "{importMutation.data.unknown_corpus.name}" ({importMutation.data.unknown_corpus.document_count} docs).
        </p>
      )}

      {importMutation.isError && (
        <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--danger)' }}>
          {(importMutation.error as Error).message || 'Failed to import corpus.'}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CorporaPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  // ----- queries -----------------------------------------------------------

  const {
    data: corpora = [],
    isLoading: corporaLoading,
    error: corporaError,
  } = useQuery({
    queryKey: ['corpora'],
    queryFn: corporaApi.list,
  });

  const { data: allDocuments = [] } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.list,
  });

  // ----- mutations ---------------------------------------------------------

  const createMutation = useMutation({
    mutationFn: ({ name, description }: { name: string; description?: string }) =>
      corporaApi.create(name, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['corpora'] });
      setName('');
      setDescription('');
    },
  });

  // ----- handlers ----------------------------------------------------------

  const handleCreate = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
    });
  };

  // ----- render ------------------------------------------------------------

  const createCardStyle: React.CSSProperties = {
    ...cardStyle,
    marginBottom: '1.5rem',
  };

  return (
    <div>
      <h1>Corpora</h1>

      {/* Create corpus section */}
      <div style={createCardStyle}>
        <h2 style={{ marginBottom: '0.75rem' }}>Create Corpus</h2>
        <form onSubmit={handleCreate}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', flex: '1 1 200px' }}>
              <label>Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Corpus name"
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', flex: '2 1 300px' }}>
              <label>Description (optional)</label>
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                className="primary"
                type="submit"
                disabled={!name.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </form>

        {createMutation.isError && (
          <p style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--danger)' }}>
            {(createMutation.error as Error).message || 'Failed to create corpus.'}
          </p>
        )}
      </div>

      {/* Import sample corpus section */}
      <SampleCorpusImporter />

      {/* Corpora list */}
      {corporaLoading && <p style={{ color: 'var(--text-muted)' }}>Loading corpora...</p>}

      {corporaError && (
        <p style={{ color: 'var(--danger)' }}>
          Failed to load corpora: {(corporaError as Error).message}
        </p>
      )}

      {!corporaLoading && !corporaError && corpora.length === 0 && (
        <p style={{ color: 'var(--text-muted)' }}>
          No corpora yet. Create one above to get started.
        </p>
      )}

      {corpora.map((corpus) => (
        <CorpusCard
          key={corpus.id}
          corpus={corpus}
          allDocuments={allDocuments}
        />
      ))}
    </div>
  );
}
