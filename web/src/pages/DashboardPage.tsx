import { Link, useNavigate } from 'react-router-dom';
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
// Getting Started (shown when no data exists)
// ---------------------------------------------------------------------------

function GettingStarted({ onNavigate }: { onNavigate: (path: string) => void }) {
  return (
    <div>
      <h1>Welcome to mowen</h1>
      <p className={s.welcomeDesc}>
        Authorship attribution through computational stylometry.
        Determine who wrote a document by analyzing writing style with configurable NLP pipelines.
      </p>

      <div className={s.quickStart}>
        <div className={`card ${s.quickStartCard}`}>
          <div className={s.quickStartLabel}>Quick start</div>
          <h2 style={{ marginBottom: '0.35rem' }}>Try with sample data</h2>
          <p className="muted text-sm" style={{ marginBottom: '0.75rem' }}>
            Import a pre-labeled AAAC benchmark corpus and run a classic authorship attribution method
            in under a minute.
          </p>
          <button className="primary" onClick={() => onNavigate('/corpora')}>
            Import Sample Corpus
          </button>
        </div>
      </div>

      <h2 className={s.stepsHeading}>Or start from scratch</h2>

      <div className={s.stepsGrid}>
        <div className={`card ${s.stepCard}`}>
          <div className={s.stepCardNumber}>1</div>
          <h3>Upload documents</h3>
          <p className="muted text-sm">
            Add text files with known authors (training data) and unknown documents to attribute.
          </p>
          <button onClick={() => onNavigate('/documents')}>
            Go to Documents
          </button>
        </div>

        <div className={`card ${s.stepCard}`}>
          <div className={s.stepCardNumber}>2</div>
          <h3>Organize into corpora</h3>
          <p className="muted text-sm">
            Group documents into known-author and unknown-author corpora for your experiment.
          </p>
          <button onClick={() => onNavigate('/corpora')}>
            Go to Corpora
          </button>
        </div>

        <div className={`card ${s.stepCard}`}>
          <div className={s.stepCardNumber}>3</div>
          <h3>Run an experiment</h3>
          <p className="muted text-sm">
            Choose from 17 preset pipelines or configure your own canonicizers, event drivers,
            distance functions, and analysis methods.
          </p>
          <button onClick={() => onNavigate('/experiments/new')}>
            New Experiment
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const navigate = useNavigate();

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

  const isLoading = docsLoading || corporaLoading || experimentsLoading;
  const isEmpty = !isLoading && documents.length === 0 && corpora.length === 0 && experiments.length === 0;

  // Show getting started experience for first-time users
  if (isEmpty) {
    return <GettingStarted onNavigate={navigate} />;
  }

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

      {/* Quick actions — lightweight row, not a full card */}
      <div className={s.quickActions}>
        <button className="primary" onClick={() => navigate('/documents')}>
          Upload Document
        </button>
        <button className="primary" onClick={() => navigate('/experiments/new')}>
          New Experiment
        </button>
      </div>

      {/* Recent experiments */}
      <div className="card">
        <h2>Recent Experiments</h2>

        {experimentsLoading && (
          <p className="muted text-sm">Loading experiments...</p>
        )}

        {!experimentsLoading && experiments.length === 0 && (
          <p className="muted text-sm">
            No experiments yet. Import a sample corpus on the Corpora page to try mowen with real benchmark data,
            or upload your own documents and build an experiment from scratch.
          </p>
        )}

        {!experimentsLoading && recentExperiments.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table>
              <caption className="sr-only">Recent experiments</caption>
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
                        className="text-sm"
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
