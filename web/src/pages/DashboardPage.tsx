import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../api/documents';
import { corporaApi } from '../api/corpora';
import { experimentsApi } from '../api/experiments';
import StatusBadge from '../components/StatusBadge';
import s from './DashboardPage.module.css';

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
    <div className={`card ${s.statCard}`}>
      <div className={s.statValue}>{isLoading ? '-' : value}</div>
      <div className={s.statLabel}>{label}</div>
    </div>
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
      <div className={s.statsRow}>
        <StatCard label="Documents" value={documents.length} isLoading={docsLoading} />
        <StatCard label="Corpora" value={corpora.length} isLoading={corporaLoading} />
        <StatCard label="Experiments" value={experiments.length} isLoading={experimentsLoading} />
      </div>

      {/* Quick actions */}
      <div className={`card ${s.quickActions}`}>
        <span className={s.quickActionsLabel}>Quick Actions:</span>
        <Link to="/documents">
          <button className="primary">Upload Document</button>
        </Link>
        <Link to="/experiments/new">
          <button className="primary">New Experiment</button>
        </Link>
      </div>

      <hr className="divider" />

      {/* Recent experiments */}
      <div className="card">
        <h2 style={{ marginBottom: '0.75rem' }}>Recent Experiments</h2>

        {experimentsLoading && (
          <p className="muted" style={{ fontSize: '0.85rem' }}>Loading experiments...</p>
        )}

        {!experimentsLoading && experiments.length === 0 && (
          <p className="muted" style={{ fontSize: '0.85rem' }}>
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
                    <td className={s.dateCell}>
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
