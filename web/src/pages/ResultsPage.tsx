import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { experimentsApi } from '../api/experiments';
import type { ExperimentResultResponse, ExperimentResponse } from '../types';
import s from './ResultsPage.module.css';
import StatusBadge from '../components/StatusBadge';
import ProgressBar from '../components/ProgressBar';

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
// Metrics computation helpers
// ---------------------------------------------------------------------------

interface AuthorStats {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

function computeAuthorStats(evaluated: ExperimentResultResponse[]): Map<string, AuthorStats> {
  const stats = new Map<string, { tp: number; fp: number; fn: number }>();
  for (const r of evaluated) {
    const trueAuthor = r.unknown_document.author_name!;
    const predicted = r.rankings.length > 0 ? r.rankings[0].author : '';

    if (!stats.has(trueAuthor)) stats.set(trueAuthor, { tp: 0, fp: 0, fn: 0 });
    if (predicted && !stats.has(predicted)) stats.set(predicted, { tp: 0, fp: 0, fn: 0 });

    if (predicted === trueAuthor) {
      stats.get(trueAuthor)!.tp++;
    } else {
      stats.get(trueAuthor)!.fn++;
      if (predicted) stats.get(predicted)!.fp++;
    }
  }

  const result = new Map<string, AuthorStats>();
  for (const [author, st] of stats) {
    const precision = st.tp + st.fp > 0 ? st.tp / (st.tp + st.fp) : 0;
    const recall = st.tp + st.fn > 0 ? st.tp / (st.tp + st.fn) : 0;
    const f1 = precision + recall > 0 ? (2 * precision * recall) / (precision + recall) : 0;
    result.set(author, { ...st, precision, recall, f1 });
  }
  return result;
}

/**
 * Compute macro-averaged AUROC using the trapezoidal rule.
 *
 * For each author (one-vs-rest), we use the ranking scores as a
 * confidence signal.  For distance-based methods (lower_is_better),
 * scores are negated so higher = more confident.
 */
function computeAUROC(evaluated: ExperimentResultResponse[]): number | null {
  if (evaluated.length < 2) return null;

  const allAuthors = new Set<string>();
  for (const r of evaluated) {
    allAuthors.add(r.unknown_document.author_name!);
    for (const rank of r.rankings) allAuthors.add(rank.author);
  }
  if (allAuthors.size < 2) return null;

  const lowerIsBetter = evaluated[0]?.lower_is_better ?? true;
  let totalAUC = 0;
  let counted = 0;

  for (const targetAuthor of allAuthors) {
    // Build (score, isPositive) pairs for this author
    const pairs: { score: number; positive: boolean }[] = [];
    for (const r of evaluated) {
      const isPositive = r.unknown_document.author_name === targetAuthor;
      const rankEntry = r.rankings.find((rk) => rk.author === targetAuthor);
      if (!rankEntry) continue;
      // Normalize: higher score = more confident attribution to this author
      const score = lowerIsBetter ? -rankEntry.score : rankEntry.score;
      pairs.push({ score, positive: isPositive });
    }

    const positives = pairs.filter((p) => p.positive).length;
    const negatives = pairs.length - positives;
    if (positives === 0 || negatives === 0) continue;

    // Sort descending by score
    pairs.sort((a, b) => b.score - a.score);

    // Trapezoidal AUC
    let tp = 0;
    let fp = 0;
    let auc = 0;
    let prevTPR = 0;
    let prevFPR = 0;

    for (const p of pairs) {
      if (p.positive) tp++;
      else fp++;
      const tpr = tp / positives;
      const fpr = fp / negatives;
      auc += (fpr - prevFPR) * (tpr + prevTPR) / 2;
      prevTPR = tpr;
      prevFPR = fpr;
    }

    totalAUC += auc;
    counted++;
  }

  return counted > 0 ? totalAUC / counted : null;
}

/**
 * Mean Reciprocal Rank: average of 1/rank where rank is the position
 * of the true author in the ranking list.
 */
function computeMRR(evaluated: ExperimentResultResponse[]): number | null {
  if (evaluated.length === 0) return null;
  let total = 0;
  for (const r of evaluated) {
    const trueAuthor = r.unknown_document.author_name!;
    const rank = r.rankings.findIndex((rk) => rk.author === trueAuthor);
    if (rank >= 0) {
      total += 1 / (rank + 1);
    }
    // If true author not in rankings, contributes 0
  }
  return total / evaluated.length;
}

/**
 * Compute F_0.5u: precision-weighted F-measure that credits non-answers.
 * Non-answers are predictions where verification_threshold is set and
 * the top score equals 0.5.
 */
function computeF05u(evaluated: ExperimentResultResponse[]): number | null {
  if (evaluated.length === 0) return null;

  const n = evaluated.length;
  let nc = 0;
  let nu = 0;
  for (const r of evaluated) {
    const predicted = r.rankings.length > 0 ? r.rankings[0].author : null;
    if (predicted === r.unknown_document.author_name) nc++;
    if (r.verification_threshold != null && r.rankings.length > 0 && r.rankings[0].score === 0.5) nu++;
  }

  const nAnswered = n - nu;
  if (nAnswered === 0) return nc / n;

  const tp = nc;
  const fp = nAnswered - nc;
  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = n > 0 ? tp / n : 0;
  const betaSq = 0.25;
  const f05 = precision + recall > 0
    ? (1 + betaSq) * precision * recall / (betaSq * precision + recall)
    : 0;

  if (nu > 0) {
    const answeredAcc = nAnswered > 0 ? nc / nAnswered : 0;
    return (nAnswered * f05 + nu * answeredAcc) / n;
  }
  return f05;
}

/**
 * Brier score complement: 1 - mean((confidence - label)^2).
 * Higher is better. Rewards well-calibrated probability outputs.
 */
function computeBrier(evaluated: ExperimentResultResponse[]): number | null {
  if (evaluated.length === 0) return null;
  // Only compute when scores are available (non-empty rankings)
  if (evaluated.some((r) => r.rankings.length === 0)) return null;

  const lowerIsBetter = evaluated[0]?.lower_is_better ?? true;
  let brierSum = 0;
  for (const r of evaluated) {
    const trueAuthor = r.unknown_document.author_name!;
    const predicted = r.rankings[0].author;
    let confidence = r.rankings[0].score;
    // For distance-based methods, lower score = more confident,
    // so we invert by taking 1 - normalized score
    if (lowerIsBetter) {
      const maxScore = Math.max(...r.rankings.map((rk) => rk.score));
      confidence = maxScore > 0 ? 1 - confidence / maxScore : 0;
    }
    confidence = Math.max(0, Math.min(1, confidence));
    const label = predicted === trueAuthor ? 1 : 0;
    brierSum += (confidence - label) ** 2;
  }
  return 1 - brierSum / evaluated.length;
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

      {/* Top-level metrics */}
      <div className={s.metricsGrid}>
        <div className={s.metricCell}>
          <div className={s.metricValue} style={{ color: accuracy >= 0.5 ? 'var(--success)' : 'var(--danger)' }}>
            {fmtPct(accuracy)}
          </div>
          <div className={s.metricLabel}>Accuracy</div>
        </div>
        <div className={s.metricCell}>
          <div className={s.metricValue} style={{ color: 'var(--text)' }}>{fmtPct(macroPrecision)}</div>
          <div className={s.metricLabel}>Precision</div>
        </div>
        <div className={s.metricCell}>
          <div className={s.metricValue} style={{ color: 'var(--text)' }}>{fmtPct(macroRecall)}</div>
          <div className={s.metricLabel}>Recall</div>
        </div>
        <div className={s.metricCell}>
          <div className={s.metricValue} style={{ color: 'var(--text)' }}>{fmtPct(macroF1)}</div>
          <div className={s.metricLabel}>F1</div>
        </div>
        {auroc != null && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--text)' }}>{auroc.toFixed(3)}</div>
            <div className={s.metricLabel}>AUROC</div>
          </div>
        )}
        {mrr != null && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--text)' }}>{mrr.toFixed(3)}</div>
            <div className={s.metricLabel}>MRR</div>
          </div>
        )}
        {f05u != null && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--text)' }}>{f05u.toFixed(3)}</div>
            <div className={s.metricLabel}>F0.5u</div>
          </div>
        )}
        {brier != null && (
          <div className={s.metricCell}>
            <div className={s.metricValue} style={{ color: 'var(--text)' }}>{brier.toFixed(3)}</div>
            <div className={s.metricLabel}>Brier</div>
          </div>
        )}
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
      <table style={{ fontSize: '0.85rem' }}>
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
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No rankings available.</p>
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
              <p style={{ color: 'var(--text)', fontSize: '0.9rem' }}>
                Experiment is running...
              </p>
              <ProgressBar progress={experiment.progress} />
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.75rem' }}>
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
        <AttributionTable key={result.unknown_document.id ?? idx} result={result} />
      ))}
    </div>
  );
}
