import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../api/documents';
import { corporaApi } from '../api/corpora';
import { experimentsApi } from '../api/experiments';
import type { ExperimentResponse } from '../types';

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const cardStyle: React.CSSProperties = {
  background: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  padding: '1.25rem',
  marginBottom: '1rem',
};

// ---------------------------------------------------------------------------
// Stat Card
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  isLoading,
}: {
  label: string;
  value: number;
  isLoading: boolean;
}) {
  return (
    <div
      style={{
        ...cardStyle,
        flex: '1 1 200px',
        textAlign: 'center',
        marginBottom: 0,
      }}
    >
      <div
        style={{
          fontSize: '2rem',
          fontWeight: 700,
          color: '#7c8cf8',
          lineHeight: 1.2,
        }}
      >
        {isLoading ? '-' : value}
      </div>
      <div
        style={{
          fontSize: '0.8rem',
          color: '#8888aa',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginTop: '0.25rem',
        }}
      >
        {label}
      </div>
    </div>
  );
}

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
        borderRadius: '10px',
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
// Main Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { data: documents = [], isLoading: docsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsApi.list,
  });

  const { data: corpora = [], isLoading: corporaLoading } = useQuery({
    queryKey: ['corpora'],
    queryFn: corporaApi.list,
  });

  const { data: experiments = [], isLoading: experimentsLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: experimentsApi.list,
  });

  // Recent experiments - sort by created_at descending, take 5
  const recentExperiments = [...experiments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div>
      <h1>Dashboard</h1>

      {/* Quick stats */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <StatCard label="Documents" value={documents.length} isLoading={docsLoading} />
        <StatCard label="Corpora" value={corpora.length} isLoading={corporaLoading} />
        <StatCard label="Experiments" value={experiments.length} isLoading={experimentsLoading} />
      </div>

      {/* Quick actions */}
      <div style={{ ...cardStyle, display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', color: '#8888aa', marginRight: '0.5rem' }}>Quick Actions:</span>
        <Link to="/documents">
          <button className="primary">Upload Document</button>
        </Link>
        <Link to="/experiments/new">
          <button className="primary">New Experiment</button>
        </Link>
      </div>

      {/* Recent experiments */}
      <div style={cardStyle}>
        <h2 style={{ marginBottom: '0.75rem' }}>Recent Experiments</h2>

        {experimentsLoading && (
          <p style={{ color: '#8888aa', fontSize: '0.85rem' }}>Loading experiments...</p>
        )}

        {!experimentsLoading && experiments.length === 0 && (
          <p style={{ color: '#8888aa', fontSize: '0.85rem' }}>
            No experiments yet. Create one to get started with authorship attribution.
          </p>
        )}

        {!experimentsLoading && recentExperiments.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentExperiments.map((exp) => (
                  <tr key={exp.id}>
                    <td style={{ fontWeight: 500 }}>{exp.name}</td>
                    <td>
                      <StatusBadge status={exp.status} />
                    </td>
                    <td style={{ color: '#8888aa', fontSize: '0.85rem' }}>
                      {new Date(exp.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <Link
                        to={`/experiments/${exp.id}/results`}
                        style={{ fontSize: '0.85rem' }}
                      >
                        View Results
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
