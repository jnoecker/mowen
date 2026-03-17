import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentsApi } from '../api/experiments';
import { useExperimentStore } from '../store/experimentStore';
import type { ExperimentResponse } from '../types';

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  padding: '1.25rem',
  marginBottom: '0.75rem',
};

// ---------------------------------------------------------------------------
// Status Badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: ExperimentResponse['status'] }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    pending: { bg: 'rgba(136, 136, 170, 0.15)', text: '#8888aa', border: '#8888aa' },
    running: { bg: 'rgba(124, 140, 248, 0.15)', text: '#7c8cf8', border: '#7c8cf8' },
    completed: { bg: 'rgba(74, 222, 128, 0.15)', text: '#4ade80', border: '#4ade80' },
    failed: { bg: 'rgba(248, 113, 113, 0.15)', text: '#f87171', border: '#f87171' },
  };
  const c = colors[status] ?? colors.pending;
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.15rem 0.5rem',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: 600,
        background: c.bg,
        color: c.text,
        border: `1px solid ${c.border}`,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
      }}
    >
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Experiment Row
// ---------------------------------------------------------------------------

function ExperimentCard({ experiment }: { experiment: ExperimentResponse }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const loadFromConfig = useExperimentStore((s) => s.loadFromConfig);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const deleteMutation = useMutation({
    mutationFn: () => experimentsApi.delete(experiment.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['experiments'] }),
  });

  const handleClone = () => {
    loadFromConfig(
      `${experiment.name} (copy)`,
      experiment.config,
      experiment.known_corpus_ids,
      experiment.unknown_corpus_ids,
    );
    navigate('/experiments/new');
  };

  const handleDelete = () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    deleteMutation.mutate();
    setConfirmDelete(false);
  };

  const configParts: string[] = [];
  if (experiment.config.event_drivers.length > 0) {
    configParts.push(experiment.config.event_drivers.map((d) => d.name).join(', '));
  }
  if (experiment.config.analysis_method) {
    configParts.push(experiment.config.analysis_method.name);
  }

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <h2
              style={{ margin: 0, fontSize: '1.05rem', cursor: 'pointer' }}
              onClick={() => navigate(`/experiments/${experiment.id}/results`)}
            >
              {experiment.name}
            </h2>
            <StatusBadge status={experiment.status} />
          </div>

          <div style={{ fontSize: '0.8rem', color: '#8888aa', display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
            {configParts.length > 0 && <span>{configParts.join(' + ')}</span>}
            <span>Created {new Date(experiment.created_at).toLocaleDateString()}</span>
            {experiment.completed_at && (
              <span>Completed {new Date(experiment.completed_at).toLocaleString()}</span>
            )}
            {experiment.status === 'running' && (
              <span>{Math.round(experiment.progress)}% complete</span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0, marginLeft: '1rem' }}>
          <button
            onClick={() => navigate(`/experiments/${experiment.id}/results`)}
            style={{ fontSize: '0.85rem', padding: '0.35rem 0.6rem' }}
          >
            View
          </button>
          <button
            onClick={handleClone}
            style={{ fontSize: '0.85rem', padding: '0.35rem 0.6rem' }}
          >
            Clone
          </button>
          <button
            onClick={handleDelete}
            onBlur={() => setConfirmDelete(false)}
            style={{
              fontSize: '0.85rem',
              padding: '0.35rem 0.6rem',
              ...(confirmDelete
                ? { background: 'var(--danger)', borderColor: 'var(--danger)', color: '#fff' }
                : {}),
            }}
          >
            {confirmDelete ? 'Confirm' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ExperimentsListPage() {
  const navigate = useNavigate();
  const reset = useExperimentStore((s) => s.reset);

  const {
    data: experiments = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['experiments'],
    queryFn: experimentsApi.list,
  });

  const handleNewExperiment = () => {
    reset();
    navigate('/experiments/new');
  };

  // Sort: most recent first
  const sorted = [...experiments].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ marginBottom: 0 }}>Experiments</h1>
        <button className="primary" onClick={handleNewExperiment}>
          New Experiment
        </button>
      </div>

      {isLoading && <p style={{ color: '#8888aa' }}>Loading experiments...</p>}

      {error && (
        <p style={{ color: 'var(--danger)' }}>
          Failed to load experiments: {(error as Error).message}
        </p>
      )}

      {!isLoading && !error && sorted.length === 0 && (
        <p style={{ color: '#8888aa' }}>
          No experiments yet. Click "New Experiment" to get started.
        </p>
      )}

      {sorted.map((exp) => (
        <ExperimentCard key={exp.id} experiment={exp} />
      ))}
    </div>
  );
}
