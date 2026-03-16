import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { experimentsApi } from '../api/experiments';
import type { ExperimentResultResponse, ExperimentResponse } from '../types';

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
        padding: '0.2rem 0.6rem',
        borderRadius: '12px',
        fontSize: '0.8rem',
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
// Progress Bar
// ---------------------------------------------------------------------------

function ProgressBar({ progress }: { progress: number }) {
  const pct = Math.min(Math.max(progress, 0), 100);
  return (
    <div style={{ marginTop: '1rem' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          color: '#8888aa',
          marginBottom: '0.35rem',
        }}
      >
        <span>Progress</span>
        <span>{Math.round(pct)}%</span>
      </div>
      <div
        style={{
          height: '8px',
          background: '#16213e',
          borderRadius: '4px',
          overflow: 'hidden',
          border: '1px solid #2a2a4a',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: 'linear-gradient(90deg, #7c8cf8, #9ba6ff)',
            borderRadius: '4px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Config Summary
// ---------------------------------------------------------------------------

function ConfigSummary({ experiment }: { experiment: ExperimentResponse }) {
  const { config } = experiment;

  const tagStyle: React.CSSProperties = {
    display: 'inline-block',
    padding: '0.15rem 0.5rem',
    background: '#16213e',
    borderRadius: '4px',
    fontSize: '0.8rem',
    border: '1px solid #2a2a4a',
    marginRight: '0.35rem',
    marginBottom: '0.25rem',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: '0.75rem',
    color: '#8888aa',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
    marginBottom: '0.25rem',
    marginTop: '0.5rem',
  };

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', fontSize: '0.85rem' }}>
      {config.canonicizers.length > 0 && (
        <div>
          <div style={labelStyle}>Canonicizers</div>
          {config.canonicizers.map((c) => (
            <span key={c.name} style={tagStyle}>{c.name}</span>
          ))}
        </div>
      )}
      <div>
        <div style={labelStyle}>Event Drivers</div>
        {config.event_drivers.map((c) => (
          <span key={c.name} style={tagStyle}>{c.name}</span>
        ))}
      </div>
      {config.event_cullers.length > 0 && (
        <div>
          <div style={labelStyle}>Event Cullers</div>
          {config.event_cullers.map((c) => (
            <span key={c.name} style={tagStyle}>{c.name}</span>
          ))}
        </div>
      )}
      {config.distance_function && (
        <div>
          <div style={labelStyle}>Distance Function</div>
          <span style={tagStyle}>{config.distance_function.name}</span>
        </div>
      )}
      <div>
        <div style={labelStyle}>Analysis Method</div>
        <span style={tagStyle}>{config.analysis_method.name}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Attribution Table for a single unknown document
// ---------------------------------------------------------------------------

function AttributionTable({ result }: { result: ExperimentResultResponse }) {
  const { unknown_document, rankings } = result;

  // Find the maximum score to scale bars
  const maxScore = rankings.length > 0 ? Math.max(...rankings.map((r) => Math.abs(r.score))) : 1;
  const topAuthor = rankings.length > 0 ? rankings[0].author : null;

  return (
    <div style={cardStyle}>
      <h3 style={{ marginBottom: '0.75rem', color: '#e0e0e0' }}>
        {unknown_document.title}
        {unknown_document.author_name && (
          <span style={{ fontSize: '0.8rem', color: '#8888aa', fontWeight: 'normal', marginLeft: '0.5rem' }}>
            (actual: {unknown_document.author_name})
          </span>
        )}
      </h3>

      {rankings.length === 0 ? (
        <p style={{ color: '#8888aa', fontSize: '0.85rem' }}>No rankings available.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{ width: '40px' }}>Rank</th>
              <th>Author</th>
              <th style={{ width: '100px', textAlign: 'right' }}>Score</th>
              <th>Distribution</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((entry, idx) => {
              const isTop = entry.author === topAuthor;
              const barWidth = maxScore > 0 ? (Math.abs(entry.score) / maxScore) * 100 : 0;

              return (
                <tr
                  key={entry.author}
                  style={{
                    background: isTop ? 'rgba(124, 140, 248, 0.08)' : undefined,
                  }}
                >
                  <td
                    style={{
                      fontWeight: isTop ? 700 : 400,
                      color: isTop ? '#7c8cf8' : '#e0e0e0',
                      textAlign: 'center',
                    }}
                  >
                    {idx + 1}
                  </td>
                  <td
                    style={{
                      fontWeight: isTop ? 600 : 400,
                      color: isTop ? '#7c8cf8' : '#e0e0e0',
                    }}
                  >
                    {entry.author}
                  </td>
                  <td
                    style={{
                      textAlign: 'right',
                      fontFamily: 'monospace',
                      fontSize: '0.85rem',
                      color: isTop ? '#7c8cf8' : '#e0e0e0',
                    }}
                  >
                    {entry.score.toFixed(4)}
                  </td>
                  <td style={{ paddingLeft: '0.75rem' }}>
                    <div
                      style={{
                        height: '16px',
                        background: '#16213e',
                        borderRadius: '3px',
                        overflow: 'hidden',
                        position: 'relative',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${barWidth}%`,
                          background: isTop
                            ? 'linear-gradient(90deg, #7c8cf8, #9ba6ff)'
                            : 'linear-gradient(90deg, #3a3a5a, #4a4a6a)',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease',
                          minWidth: barWidth > 0 ? '2px' : '0',
                        }}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const experimentId = Number(id);

  // Fetch experiment details
  const {
    data: experiment,
    isLoading: experimentLoading,
    error: experimentError,
  } = useQuery({
    queryKey: ['experiments', experimentId],
    queryFn: () => experimentsApi.get(experimentId),
    enabled: !isNaN(experimentId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'pending' || data.status === 'running')) {
        return 2000;
      }
      return false;
    },
  });

  // Fetch results only when completed
  const {
    data: results = [],
    isLoading: resultsLoading,
  } = useQuery({
    queryKey: ['experiments', experimentId, 'results'],
    queryFn: () => experimentsApi.getResults(experimentId),
    enabled: experiment?.status === 'completed',
  });

  // ----- loading / error states --------------------------------------------

  if (isNaN(experimentId)) {
    return (
      <div>
        <h1>Results</h1>
        <p style={{ color: '#f87171' }}>Invalid experiment ID.</p>
      </div>
    );
  }

  if (experimentLoading) {
    return (
      <div>
        <h1>Results</h1>
        <p style={{ color: '#8888aa' }}>Loading experiment...</p>
      </div>
    );
  }

  if (experimentError) {
    return (
      <div>
        <h1>Results</h1>
        <div
          style={{
            ...cardStyle,
            borderColor: '#f87171',
          }}
        >
          <p style={{ color: '#f87171' }}>
            Failed to load experiment: {(experimentError as Error).message}
          </p>
        </div>
      </div>
    );
  }

  if (!experiment) {
    return (
      <div>
        <h1>Results</h1>
        <p style={{ color: '#8888aa' }}>Experiment not found.</p>
      </div>
    );
  }

  // ----- non-completed states ----------------------------------------------

  if (experiment.status !== 'completed') {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <h1 style={{ marginBottom: 0 }}>{experiment.name}</h1>
          <StatusBadge status={experiment.status} />
        </div>

        <div style={cardStyle}>
          <ConfigSummary experiment={experiment} />
        </div>

        <div style={cardStyle}>
          {experiment.status === 'pending' && (
            <div>
              <p style={{ color: '#8888aa', fontSize: '0.9rem' }}>
                This experiment is queued and waiting to start.
              </p>
              <p style={{ color: '#8888aa', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                This page will update automatically when the experiment begins.
              </p>
            </div>
          )}

          {experiment.status === 'running' && (
            <div>
              <p style={{ color: '#e0e0e0', fontSize: '0.9rem' }}>
                Experiment is running...
              </p>
              <ProgressBar progress={experiment.progress} />
              <p style={{ color: '#8888aa', fontSize: '0.8rem', marginTop: '0.75rem' }}>
                This page updates automatically every 2 seconds.
              </p>
            </div>
          )}

          {experiment.status === 'failed' && (
            <div>
              <p style={{ color: '#f87171', fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Experiment Failed
              </p>
              {experiment.error_message && (
                <div
                  style={{
                    padding: '0.75rem 1rem',
                    background: 'rgba(248, 113, 113, 0.1)',
                    border: '1px solid rgba(248, 113, 113, 0.3)',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    color: '#f87171',
                    fontFamily: 'monospace',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {experiment.error_message}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ----- completed state ---------------------------------------------------

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <h1 style={{ marginBottom: 0 }}>{experiment.name}</h1>
        <StatusBadge status={experiment.status} />
      </div>

      {/* Config summary */}
      <div style={cardStyle}>
        <ConfigSummary experiment={experiment} />
        <div
          style={{
            display: 'flex',
            gap: '1.5rem',
            marginTop: '0.75rem',
            paddingTop: '0.75rem',
            borderTop: '1px solid #2a2a4a',
            fontSize: '0.8rem',
            color: '#8888aa',
          }}
        >
          {experiment.started_at && (
            <span>Started: {new Date(experiment.started_at).toLocaleString()}</span>
          )}
          {experiment.completed_at && (
            <span>Completed: {new Date(experiment.completed_at).toLocaleString()}</span>
          )}
        </div>
      </div>

      {/* Results */}
      <h2 style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>
        Attribution Results
        <span style={{ fontSize: '0.85rem', color: '#8888aa', fontWeight: 'normal', marginLeft: '0.5rem' }}>
          ({results.length} document{results.length !== 1 ? 's' : ''})
        </span>
      </h2>

      {resultsLoading && <p style={{ color: '#8888aa' }}>Loading results...</p>}

      {!resultsLoading && results.length === 0 && (
        <p style={{ color: '#8888aa' }}>No results available.</p>
      )}

      {results.map((result, idx) => (
        <AttributionTable key={result.unknown_document.id ?? idx} result={result} />
      ))}
    </div>
  );
}
