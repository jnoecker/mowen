/**
 * Client-side evaluation metric computation.
 *
 * These functions operate on experiment result arrays and compute
 * standard information-retrieval and verification metrics.
 */

import type { ExperimentResultResponse } from './types';

// ---------------------------------------------------------------------------
// Per-author statistics
// ---------------------------------------------------------------------------

export interface AuthorStats {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

export function computeAuthorStats(evaluated: ExperimentResultResponse[]): Map<string, AuthorStats> {
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

// ---------------------------------------------------------------------------
// AUROC
// ---------------------------------------------------------------------------

/**
 * Compute macro-averaged AUROC using the trapezoidal rule.
 *
 * For each author (one-vs-rest), we use the ranking scores as a
 * confidence signal.  For distance-based methods (lower_is_better),
 * scores are negated so higher = more confident.
 */
export function computeAUROC(evaluated: ExperimentResultResponse[]): number | null {
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

// ---------------------------------------------------------------------------
// MRR
// ---------------------------------------------------------------------------

/**
 * Mean Reciprocal Rank: average of 1/rank where rank is the position
 * of the true author in the ranking list.
 */
export function computeMRR(evaluated: ExperimentResultResponse[]): number | null {
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

// ---------------------------------------------------------------------------
// F_0.5u
// ---------------------------------------------------------------------------

/**
 * Compute F_0.5u: precision-weighted F-measure that credits non-answers.
 * Non-answers are predictions where verification_threshold is set and
 * the top score equals 0.5.
 */
export function computeF05u(evaluated: ExperimentResultResponse[]): number | null {
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

// ---------------------------------------------------------------------------
// Brier score
// ---------------------------------------------------------------------------

/**
 * Brier score complement: 1 - mean((confidence - label)^2).
 * Higher is better. Rewards well-calibrated probability outputs.
 */
export function computeBrier(evaluated: ExperimentResultResponse[]): number | null {
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
