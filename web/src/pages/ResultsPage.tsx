import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import { experimentsApi } from '../api/experiments';
import { computeAuthorStats, computeAUROC, computeMRR, computeF05u, computeBrier } from '../metrics';
import type { ExperimentResultResponse, ExperimentResponse } from '../types';
import s from './ResultsPage.module.css';
import StatusBadge from '../components/StatusBadge';
import ProgressBar from '../components/ProgressBar';

// ---------------------------------------------------------------------------
// Counting animation hook — animates a number from 0 to target
// ---------------------------------------------------------------------------

function useCountUp(target: number, duration = 600): string {
  const [display, setDisplay] = useState('0');
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const isPercent = target <= 1 && target >= 0;
    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out quad
      const eased = 1 - (1 - progress) * (1 - progress);
      const current = target * eased;

      if (isPercent) {
        setDisplay(`${(current * 100).toFixed(1)}%`);
      } else if (Number.isInteger(target)) {
        setDisplay(String(Math.round(current)));
      } else {
        setDisplay(current.toFixed(3));
      }

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    // Respect reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      if (isPercent) setDisplay(`${(target * 100).toFixed(1)}%`);
      else if (Number.isInteger(target)) setDisplay(String(target));
      else setDisplay(target.toFixed(3));
      return;
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return display;
}

function CountingMetric({ value, color, label }: { value: number; color?: string; label: string }) {
  const display = useCountUp(value);
  return (
    <div className={s.metricCell}>
      <div className={s.metricValue} style={color ? { color } : undefined}>{display}</div>
      <div className={s.metricLabel}>{label}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Config Summary
// ---------------------------------------------------------------------------

function ConfigSummary({ experiment }: { experiment: ExperimentResponse }) {
  const { config } = experiment;

  return (
    <div className={s.configWrap}>
      {config.canonicizers.length > 0 && (
        <div>
          <div className="section-label">Canonicizers</div>
          {config.canonicizers.map((c) => (
            <span key={c.name} className="tag">{c.name}</span>
          ))}
        </div>
      )}
      <div>
        <div className="section-label">Event Drivers</div>
        {config.event_drivers.map((c) => (
          <span key={c.name} className="tag">{c.name}</span>
        ))}
      </div>
      {config.event_cullers.length > 0 && (
        <div>
          <div className="section-label">Event Cullers</div>
          {config.event_cullers.map((c) => (
            <span key={c.name} className="tag">{c.name}</span>
          ))}
        </div>
      )}
      {config.distance_function && (
        <div>
          <div className="section-label">Distance Function</div>
          <span className="tag">{config.distance_function.name}</span>
        </div>
      )}
      <div>
        <div className="section-label">Analysis Method</div>
        <span className="tag">{config.analysis_method.name}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Performance Summary (shown when ground truth is available)
// ---------------------------------------------------------------------------

function PerformanceSummary({ results }: { results: ExperimentResultResponse[] }) {
  const evaluated = results.filter((r) => r.unknown_document.author_name != null);
  if (evaluated.length === 0) return null;

  const correct = evaluated.filter((r) => {
    const predicted = r.rankings.length > 0 ? r.rankings[0].author : null;
    return predicted === r.unknown_document.author_name;
  });

  const accuracy = correct.length / evaluated.length;
  const unevaluated = results.length - evaluated.length;

  const authorStats = computeAuthorStats(evaluated);
  const sortedAuthors = [...authorStats.entries()].sort((a, b) => a[0].localeCompare(b[0]));

  // Macro-averaged metrics (equal weight per class)
  const allStats = [...authorStats.values()];
  const macroPrecision = allStats.reduce((sum, a) => sum + a.precision, 0) / allStats.length;
  const macroRecall = allStats.reduce((sum, a) => sum + a.recall, 0) / allStats.length;
  const macroF1 = allStats.reduce((sum, a) => sum + a.f1, 0) / allStats.length;

  const auroc = computeAUROC(evaluated);
  const mrr = computeMRR(evaluated);
  const f05u = computeF05u(evaluated);
  const brier = computeBrier(evaluated);

  // Verification metrics (only when threshold is present)
  const hasVerification = evaluated.some((r) => r.verification_threshold != null);
  let verifiedCount: number | null = null;
  let rejectedCount: number | null = null;
  let inconclusiveCount: number | null = null;
  if (hasVerification) {
    inconclusiveCount = evaluated.filter(
      (r) => r.verification_threshold != null && r.rankings.length > 0 && r.rankings[0].score === 0.5
    ).length;
    verifiedCount = evaluated.filter(
      (r) => r.verification_threshold != null && r.rankings.length > 0 && r.rankings[0].score !== 0.5 && r.rankings[0].score >= r.verification_threshold
    ).length;
    rejectedCount = evaluated.length - verifiedCount - inconclusiveCount;
  }

  const fmtPct = (v: number) => `${(v * 100).toFixed(1)}%`;

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <h2 style={{ marginBottom: '1rem' }}>Performance</h2>

      {/* Top-level metrics — counting animation on mount */}
      <div className={s.metricsGrid}>
        <CountingMetric value={accuracy} color={accuracy >= 0.5 ? 'var(--success)' : 'var(--danger)'} label="Accuracy" />
        <CountingMetric value={macroPrecision} label="Precision" />
        <CountingMetric value={macroRecall} label="Recall" />
        <CountingMetric value={macroF1} label="F1" />
        {auroc != null && <CountingMetric value={auroc} label="AUROC" />}
        {mrr != null && <CountingMetric value={mrr} label="MRR" />}
        {f05u != null && <CountingMetric value={f05u} label="F0.5u" />}
        {brier != null && <CountingMetric value={brier} label="Brier" />}
        <div className={s.metricCell}>
          <div className={s.metricValue} style={{ color: 'var(--success)' }}>{correct.length}/{evaluated.length}</div>
          <div className={s.metricLabel}>Correct</div>
        </div>
        {verifiedCount != null && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--success)' }}>{verifiedCount}</div>
            <div className={s.metricLabel}>Verified</div>
          </div>
        )}
        {rejectedCount != null && rejectedCount > 0 && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--danger)' }}>{rejectedCount}</div>
            <div className={s.metricLabel}>Rejected</div>
          </div>
        )}
        {inconclusiveCount != null && inconclusiveCount > 0 && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--text-muted)' }}>{inconclusiveCount}</div>
            <div className={s.metricLabel}>Inconclusive</div>
          </div>
        )}
      </div>

      <div className={s.metricsNote}>
        Precision, Recall, and F1 are macro-averaged (equal weight per author).
        {unevaluated > 0 && (
          <> {unevaluated} document{unevaluated !== 1 ? 's' : ''} without ground truth excluded.</>
        )}
      </div>

      {/* Per-author table */}
      <table className="text-sm">
        <caption className="sr-only">Per-author performance metrics</caption>
        <thead>
          <tr>
            <th>Author</th>
            <th style={{ textAlign: 'center', width: '50px' }}>TP</th>
            <th style={{ textAlign: 'center', width: '50px' }}>FP</th>
            <th style={{ textAlign: 'center', width: '50px' }}>FN</th>
            <th style={{ textAlign: 'right', width: '80px' }}>Precision</th>
            <th style={{ textAlign: 'right', width: '80px' }}>Recall</th>
            <th style={{ textAlign: 'right', width: '80px' }}>F1</th>
          </tr>
        </thead>
        <tbody>
          {sortedAuthors.map(([author, stats]) => (
            <tr key={author}>
              <td>{author}</td>
              <td style={{ textAlign: 'center', color: 'var(--success)' }}>{stats.tp}</td>
              <td style={{ textAlign: 'center', color: stats.fp > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{stats.fp}</td>
              <td style={{ textAlign: 'center', color: stats.fn > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{stats.fn}</td>
              <td className={s.scoreCell}>{fmtPct(stats.precision)}</td>
              <td className={s.scoreCell}>{fmtPct(stats.recall)}</td>
              <td className={s.scoreCell}>{fmtPct(stats.f1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
  const trueAuthor = unknown_document.author_name;
  const isCorrect = trueAuthor != null && topAuthor === trueAuthor;
  const isIncorrect = trueAuthor != null && topAuthor !== trueAuthor;

  const threshold = result.verification_threshold;
  const isInconclusive = threshold != null && rankings.length > 0 && rankings[0].score === 0.5;
  const isVerified = threshold != null && rankings.length > 0 && !isInconclusive && rankings[0].score >= threshold;
  const isRejected = threshold != null && rankings.length > 0 && !isInconclusive && rankings[0].score < threshold;

  const cardClass = ['card', isCorrect ? s.attrCardCorrect : isIncorrect ? s.attrCardIncorrect : s.attrCard].join(' ');

  return (
    <div className={cardClass}>
      <h3 className={s.attrTitle}>
        <span>{unknown_document.title}</span>
        {trueAuthor && (
          <span className={s.attrActual}>
            (actual: {trueAuthor})
          </span>
        )}
        {isCorrect && (
          <span className={s.attrCorrect}>CORRECT</span>
        )}
        {isIncorrect && (
          <span className={s.attrIncorrect}>INCORRECT</span>
        )}
        {isVerified && (
          <span className={s.attrVerified}>VERIFIED</span>
        )}
        {isRejected && (
          <span className={s.attrRejected}>REJECTED</span>
        )}
        {isInconclusive && (
          <span className={s.attrInconclusive}>INCONCLUSIVE</span>
        )}
      </h3>

      {rankings.length === 0 ? (
        <p className="muted text-sm">No rankings available.</p>
      ) : (
        <table>
          <caption className="sr-only">
            Author attribution rankings for {unknown_document.title}
          </caption>
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
              const isTrue = trueAuthor != null && entry.author === trueAuthor;
              const barWidth = maxScore > 0 ? (Math.abs(entry.score) / maxScore) * 100 : 0;

              // Determine row class and color
              let rowColor = 'var(--text)';
              let rowClass: string | undefined;
              if (isTrue && isTop) {
                rowColor = 'var(--success)';
                rowClass = s.rowCorrectTop;
              } else if (isTop && !trueAuthor) {
                rowColor = 'var(--accent)';
                rowClass = s.rowAccentTop;
              } else if (isTop) {
                rowColor = 'var(--danger)';
                rowClass = s.rowIncorrectTop;
              } else if (isTrue) {
                rowColor = 'var(--success)';
                rowClass = s.rowTrueAuthor;
              }

              // Determine bar gradient class
              let barClass: string;
              if (isTrue) {
                barClass = s.barSuccess;
              } else if (isTop && !trueAuthor) {
                barClass = s.barAccent;
              } else if (isTop) {
                barClass = s.barDanger;
              } else {
                barClass = s.barDefault;
              }

              return (
                <tr key={entry.author} className={rowClass}>
                  <td
                    style={{
                      fontWeight: isTop || isTrue ? 700 : 400,
                      color: rowColor,
                      textAlign: 'center',
                    }}
                  >
                    {idx + 1}
                  </td>
                  <td style={{ fontWeight: isTop || isTrue ? 600 : 400, color: rowColor }}>
                    {entry.author}
                    {isTrue && !isTop && (
                      <span className={s.trueAuthorNote}>
                        (true author)
                      </span>
                    )}
                  </td>
                  <td className={s.scoreCell} style={{ color: rowColor }}>
                    {entry.score.toFixed(4)}
                  </td>
                  <td className={s.barCell}>
                    <div className="score-bar">
                      <div
                        className={`score-bar__fill ${barClass}`}
                        style={{
                          width: `${barWidth}%`,
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
        <p style={{ color: 'var(--danger)' }}>Invalid experiment ID.</p>
      </div>
    );
  }

  if (experimentLoading) {
    return (
      <div>
        <h1>Results</h1>
        <p style={{ color: 'var(--text-muted)' }}>Loading experiment...</p>
      </div>
    );
  }

  if (experimentError) {
    return (
      <div>
        <h1>Results</h1>
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)' }}>
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
        <p style={{ color: 'var(--text-muted)' }}>Experiment not found.</p>
      </div>
    );
  }

  // ----- non-completed states ----------------------------------------------

  if (experiment.status !== 'completed') {
    return (
      <div>
        <div className={s.titleRow}>
          <h1 style={{ marginBottom: 0 }}>{experiment.name}</h1>
          <StatusBadge status={experiment.status} />
        </div>

        <div className="card">
          <ConfigSummary experiment={experiment} />
        </div>

        <div className="card">
          {experiment.status === 'pending' && (
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                This experiment is queued and waiting to start.
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                This page will update automatically when the experiment begins.
              </p>
            </div>
          )}

          {experiment.status === 'running' && (
            <div>
              <p className="text-base">
                {experiment.progress < 10
                  ? 'Preparing pipeline\u2026'
                  : experiment.progress < 25
                    ? 'Canonicizing documents\u2026'
                    : experiment.progress < 50
                      ? 'Extracting stylometric features\u2026'
                      : experiment.progress < 70
                        ? 'Computing distance matrices\u2026'
                        : experiment.progress < 90
                          ? 'Running attribution analysis\u2026'
                          : 'Finalizing results\u2026'}
              </p>
              <ProgressBar progress={experiment.progress} />
              <p className="muted" style={{ fontSize: '0.8rem', marginTop: '0.75rem' }}>
                This page updates automatically every 2 seconds.
              </p>
            </div>
          )}

          {experiment.status === 'failed' && (
            <div>
              <p style={{ color: 'var(--danger)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Experiment Failed
              </p>
              {experiment.error_message && (
                <div className={s.errorBlock}>
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
      <div className={s.titleRow}>
        <h1 style={{ marginBottom: 0 }}>{experiment.name}</h1>
        <StatusBadge status={experiment.status} />
      </div>

      {/* Config summary */}
      <div className="card">
        <ConfigSummary experiment={experiment} />
        <div className={s.configMeta}>
          {experiment.started_at && (
            <span>Started: {new Date(experiment.started_at).toLocaleString()}</span>
          )}
          {experiment.completed_at && (
            <span>Completed: {new Date(experiment.completed_at).toLocaleString()}</span>
          )}
        </div>
      </div>

      {/* Performance summary (when ground truth is available) */}
      {!resultsLoading && results.length > 0 && (
        <PerformanceSummary results={results} />
      )}

      {/* Results */}
      <h2 className={s.resultsHeading}>
        Attribution Results
        <span className={s.resultsCount}>
          ({results.length} document{results.length !== 1 ? 's' : ''})
        </span>
      </h2>

      {resultsLoading && <p style={{ color: 'var(--text-muted)' }}>Loading results...</p>}

      {!resultsLoading && results.length === 0 && (
        <p style={{ color: 'var(--text-muted)' }}>No results available.</p>
      )}

      {results.map((result, idx) => (
        <div
          key={result.unknown_document.id ?? idx}
          className={s.attrReveal}
          style={{ animationDelay: `${idx * 60}ms` }}
        >
          <AttributionTable result={result} />
        </div>
      ))}

      {/* Direction C: Scroll progress indicator (scroll-driven, progressive enhancement) */}
      {results.length > 2 && (
        <div className={s.scrollProgress}>
          <div className={s.scrollProgressFill} />
        </div>
      )}
    </div>
  );
}
