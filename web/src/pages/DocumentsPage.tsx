import { useId, useState, useRef, type FormEvent } from 'react';
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
          <label>
            <span className="sr-only">Title</span>
            <input
              className={s.editInput}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
        ) : (
          doc.title
        )}
      </td>
      <td>
        {editing ? (
          <label>
            <span className="sr-only">Author</span>
            <input
              className={s.editInput}
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Unknown"
            />
          </label>
        ) : (
          <span className={doc.author_name ? undefined : s.authorUnknown}>
            {doc.author_name || 'Unknown'}
          </span>
        )}
      </td>
      <td>{doc.file_type}</td>
      <td>{doc.char_count.toLocaleString()} chars</td>
      <td>{new Date(doc.created_at).toLocaleDateString()}</td>
      <td>
        <div className="actions-row">
          {editing ? (
            <>
              <button className="primary" onClick={save}>
                Save
              </button>
              <button onClick={cancel}>Cancel</button>
            </>
          ) : confirmDelete ? (
            <>
              <span className="muted text-sm">Delete this document?</span>
              <button className="danger" onClick={handleDelete}>
                Confirm Delete
              </button>
              <button onClick={() => setConfirmDelete(false)}>Cancel</button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)}>Edit</button>
              <button onClick={handleDelete}>Delete</button>
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
  const fileId = useId();
  const titleId = useId();
  const authorId = useId();
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
      <div className={`card ${s.sectionCard}`}>
        <h2>Upload Document</h2>
        <form onSubmit={handleUpload}>
          <div className="form-row">
            <div className={s.field}>
              <label htmlFor={fileId}>File</label>
              <input id={fileId} ref={fileRef} type="file" onChange={handleFileChange} />
            </div>
            <div className={s.field}>
              <label htmlFor={titleId}>Title</label>
              <input
                id={titleId}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Document title"
              />
            </div>
            <div className={s.field}>
              <label htmlFor={authorId}>Author (optional)</label>
              <input
                id={authorId}
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Author name"
              />
            </div>
            <div className="submit-wrap">
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

        <div aria-live="polite">
          {feedback && (
            <p
              className={`text-sm ${s.feedback} ${feedback.type === 'success' ? s.feedbackSuccess : s.feedbackError}`}
              role={feedback.type === 'error' ? 'alert' : undefined}
            >
              {feedback.message}
            </p>
          )}
        </div>
      </div>

      {/* Documents table */}
      <div className="card">
        <h2>All Documents</h2>

        {isLoading && <p className="muted text-sm">Loading documents...</p>}

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
          <div className="table-scroll">
            <table>
              <caption className="sr-only">All documents</caption>
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
