import { useState, useRef, type FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../api/documents';
import type { DocumentResponse } from '../types';
import s from './DocumentsPage.module.css';

// ---------------------------------------------------------------------------
// Inline-editable document row
// ---------------------------------------------------------------------------

function DocumentRow({
  doc,
  onUpdate,
  onDelete,
}: {
  doc: DocumentResponse;
  onUpdate: (id: number, data: { title?: string; author_name?: string | null }) => void;
  onDelete: (id: number) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(doc.title);
  const [author, setAuthor] = useState(doc.author_name ?? '');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const save = () => {
    onUpdate(doc.id, {
      title,
      author_name: author || null,
    });
    setEditing(false);
  };

  const cancel = () => {
    setTitle(doc.title);
    setAuthor(doc.author_name ?? '');
    setEditing(false);
  };

  const handleDelete = () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    onDelete(doc.id);
    setConfirmDelete(false);
  };

  return (
    <tr>
      <td>
        {editing ? (
          <input
            className={s.editInput}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        ) : (
          doc.title
        )}
      </td>
      <td>
        {editing ? (
          <input
            className={s.editInput}
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Unknown"
          />
        ) : (
          <span style={{ color: doc.author_name ? 'var(--text)' : 'var(--text-muted)' }}>
            {doc.author_name || 'Unknown'}
          </span>
        )}
      </td>
      <td>{doc.file_type}</td>
      <td>{doc.char_count.toLocaleString()} chars</td>
      <td>{new Date(doc.created_at).toLocaleDateString()}</td>
      <td>
        <div className={s.actionsCell}>
          {editing ? (
            <>
              <button className="primary" onClick={save}>
                Save
              </button>
              <button onClick={cancel}>Cancel</button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)}>Edit</button>
              <button
                className={confirmDelete ? 'danger' : undefined}
                onClick={handleDelete}
                onBlur={() => setConfirmDelete(false)}
              >
                {confirmDelete ? 'Confirm' : 'Delete'}
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(
    null,
  );

  // ----- queries -----------------------------------------------------------

  const {
    data: documents = [],
    isLoading,
    error: fetchError,
  } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.list,
  });

  // ----- mutations ---------------------------------------------------------

  const uploadMutation = useMutation({
    mutationFn: ({ file, title, author }: { file: File; title: string; author?: string }) =>
      documentsApi.upload(file, title, author),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setTitle('');
      setAuthor('');
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = '';
      setFeedback({ type: 'success', message: 'Document uploaded successfully.' });
    },
    onError: (err: Error) => {
      setFeedback({ type: 'error', message: err.message || 'Upload failed.' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { title?: string; author_name?: string | null };
    }) => documentsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
    onError: (err: Error) => {
      setFeedback({ type: 'error', message: err.message || 'Update failed.' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => documentsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
    onError: (err: Error) => {
      setFeedback({ type: 'error', message: err.message || 'Delete failed.' });
    },
  });

  // ----- handlers ----------------------------------------------------------

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    if (file && !title) {
      setTitle(file.name.replace(/\.[^.]+$/, ''));
    }
  };

  const handleUpload = (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !title.trim()) return;
    setFeedback(null);
    uploadMutation.mutate({
      file: selectedFile,
      title: title.trim(),
      author: author.trim() || undefined,
    });
  };

  // ----- render ------------------------------------------------------------

  return (
    <div>
      <h1>Documents</h1>

      {/* Upload section */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ marginBottom: '0.75rem' }}>Upload Document</h2>
        <form onSubmit={handleUpload}>
          <div className={s.formRow}>
            <div className={s.field}>
              <label>File</label>
              <input ref={fileRef} type="file" onChange={handleFileChange} />
            </div>
            <div className={s.field}>
              <label>Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Document title"
              />
            </div>
            <div className={s.field}>
              <label>Author (optional)</label>
              <input
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Author name"
              />
            </div>
            <div className={s.submitWrap}>
              <button
                className="primary"
                type="submit"
                disabled={!selectedFile || !title.trim() || uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </form>

        {feedback && (
          <p
            style={{
              marginTop: '0.75rem',
              fontSize: '0.85rem',
              color: feedback.type === 'success' ? 'var(--success)' : 'var(--danger)',
            }}
          >
            {feedback.message}
          </p>
        )}
      </div>

      {/* Documents table */}
      <div className="card">
        <h2 style={{ marginBottom: '0.75rem' }}>All Documents</h2>

        {isLoading && <p className="muted">Loading documents...</p>}

        {fetchError && (
          <p style={{ color: 'var(--danger)' }}>
            Failed to load documents: {(fetchError as Error).message}
          </p>
        )}

        {!isLoading && !fetchError && documents.length === 0 && (
          <p className="muted">
            No documents yet. Upload one above to get started.
          </p>
        )}

        {!isLoading && documents.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <DocumentRow
                    key={doc.id}
                    doc={doc}
                    onUpdate={(id, data) => updateMutation.mutate({ id, data })}
                    onDelete={(id) => deleteMutation.mutate(id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
