import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentsApi } from '../api/experiments';
import { useExperimentStore } from '../store/experimentStore';
import type { ExperimentResponse } from '../types';
import StatusBadge from '../components/StatusBadge';
import s from './ExperimentsListPage.module.css';

// ---------------------------------------------------------------------------
// Experiment Row
// ---------------------------------------------------------------------------

function ExperimentCard({ experiment }: { experiment: ExperimentResponse }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const loadFromConfig = useExperimentStore((st) => st.loadFromConfig);
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
    <div className="card" style={{ marginBottom: '0.75rem' }}>
      <div className={s.cardRow}>
        <div className={s.cardContent}>
          <div className={s.cardTitle}>
            <h2
              className={s.cardName}
              onClick={() => navigate(`/experiments/${experiment.id}/results`)}
            >
              {experiment.name}
            </h2>
            <StatusBadge status={experiment.status} />
          </div>

          <div className={s.cardMeta}>
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

        <div className={s.cardActions}>
          <button
            onClick={() => navigate(`/experiments/${experiment.id}/results`)}
            className={s.smallBtn}
          >
            View
          </button>
          <button
            onClick={handleClone}
            className={s.smallBtn}
          >
            Clone
          </button>
          <button
            onClick={handleDelete}
            onBlur={() => setConfirmDelete(false)}
            className={`${s.smallBtn}${confirmDelete ? ' danger' : ''}`}
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
  const reset = useExperimentStore((st) => st.reset);

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
      <div className={s.header}>
        <h1 style={{ marginBottom: 0 }}>Experiments</h1>
        <button className="primary" onClick={handleNewExperiment}>
          New Experiment
        </button>
      </div>

      {isLoading && <p className="muted">Loading experiments...</p>}

      {error && (
        <p style={{ color: 'var(--danger)' }}>
          Failed to load experiments: {(error as Error).message}
        </p>
      )}

      {!isLoading && !error && sorted.length === 0 && (
        <p className="muted">
          No experiments yet. Click "New Experiment" to get started.
        </p>
      )}

      {sorted.map((exp) => (
        <ExperimentCard key={exp.id} experiment={exp} />
      ))}
    </div>
  );
}
