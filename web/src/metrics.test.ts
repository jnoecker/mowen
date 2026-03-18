import { describe, it, expect } from 'vitest';
import {
  computeAuthorStats,
  computeAUROC,
  computeMRR,
  computeF05u,
  computeBrier,
} from './metrics';
import type { ExperimentResultResponse, DocumentResponse } from './types';

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeDoc(author: string | null, title = 'doc'): DocumentResponse {
  return {
    id: 1,
    title,
    author_name: author,
    file_type: 'txt',
    original_filename: `${title}.txt`,
    char_count: 100,
    created_at: '',
    updated_at: '',
  };
}

function makeResult(
  trueAuthor: string,
  rankings: { author: string; score: number }[],
  opts: { lower_is_better?: boolean; verification_threshold?: number | null } = {},
): ExperimentResultResponse {
  return {
    unknown_document: makeDoc(trueAuthor),
    rankings,
    lower_is_better: opts.lower_is_better ?? true,
    verification_threshold: opts.verification_threshold ?? null,
  };
}

// ---------------------------------------------------------------------------
// computeAuthorStats
// ---------------------------------------------------------------------------

describe('computeAuthorStats', () => {
  it('computes perfect predictions', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),
      makeResult('B', [{ author: 'B', score: 0.1 }, { author: 'A', score: 0.9 }]),
    ];
    const stats = computeAuthorStats(results);
    expect(stats.get('A')!.tp).toBe(1);
    expect(stats.get('A')!.fp).toBe(0);
    expect(stats.get('A')!.fn).toBe(0);
    expect(stats.get('A')!.precision).toBe(1);
    expect(stats.get('A')!.recall).toBe(1);
    expect(stats.get('A')!.f1).toBe(1);
    expect(stats.get('B')!.tp).toBe(1);
    expect(stats.get('B')!.f1).toBe(1);
  });

  it('computes all-wrong predictions', () => {
    const results = [
      makeResult('A', [{ author: 'B', score: 0.1 }, { author: 'A', score: 0.9 }]),
      makeResult('B', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),
    ];
    const stats = computeAuthorStats(results);
    expect(stats.get('A')!.tp).toBe(0);
    expect(stats.get('A')!.fp).toBe(1);
    expect(stats.get('A')!.fn).toBe(1);
    expect(stats.get('A')!.precision).toBe(0);
    expect(stats.get('A')!.recall).toBe(0);
    expect(stats.get('A')!.f1).toBe(0);
  });

  it('handles single author', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.5 }]),
    ];
    const stats = computeAuthorStats(results);
    expect(stats.get('A')!.tp).toBe(1);
    expect(stats.get('A')!.precision).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// computeAUROC
// ---------------------------------------------------------------------------

describe('computeAUROC', () => {
  it('returns null for fewer than 2 results', () => {
    expect(computeAUROC([])).toBeNull();
    expect(computeAUROC([
      makeResult('A', [{ author: 'A', score: 0.1 }]),
    ])).toBeNull();
  });

  it('returns null for single author', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.1 }]),
      makeResult('A', [{ author: 'A', score: 0.2 }]),
    ];
    expect(computeAUROC(results)).toBeNull();
  });

  it('returns 1.0 for perfect separation (lower_is_better)', () => {
    // A's score for A is low (good), A's score for B is high (bad)
    const results = [
      makeResult('A', [
        { author: 'A', score: 0.1 },
        { author: 'B', score: 0.9 },
      ]),
      makeResult('A', [
        { author: 'A', score: 0.2 },
        { author: 'B', score: 0.8 },
      ]),
      makeResult('B', [
        { author: 'B', score: 0.1 },
        { author: 'A', score: 0.9 },
      ]),
      makeResult('B', [
        { author: 'B', score: 0.2 },
        { author: 'A', score: 0.8 },
      ]),
    ];
    const auroc = computeAUROC(results);
    expect(auroc).not.toBeNull();
    expect(auroc!).toBeCloseTo(1.0, 5);
  });

  it('returns ~0.5 for random predictions', () => {
    // Same scores for everyone — no discriminative power
    const results = [
      makeResult('A', [{ author: 'A', score: 0.5 }, { author: 'B', score: 0.5 }]),
      makeResult('B', [{ author: 'A', score: 0.5 }, { author: 'B', score: 0.5 }]),
    ];
    const auroc = computeAUROC(results);
    expect(auroc).not.toBeNull();
    expect(auroc!).toBeCloseTo(0.5, 5);
  });

  it('handles higher_is_better scores', () => {
    const results = [
      makeResult('A', [
        { author: 'A', score: 0.9 },
        { author: 'B', score: 0.1 },
      ], { lower_is_better: false }),
      makeResult('B', [
        { author: 'B', score: 0.9 },
        { author: 'A', score: 0.1 },
      ], { lower_is_better: false }),
    ];
    const auroc = computeAUROC(results);
    expect(auroc).not.toBeNull();
    expect(auroc!).toBeCloseTo(1.0, 5);
  });
});

// ---------------------------------------------------------------------------
// computeMRR
// ---------------------------------------------------------------------------

describe('computeMRR', () => {
  it('returns null for empty input', () => {
    expect(computeMRR([])).toBeNull();
  });

  it('returns 1.0 when true author is always rank 1', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),
      makeResult('B', [{ author: 'B', score: 0.1 }, { author: 'A', score: 0.9 }]),
    ];
    expect(computeMRR(results)).toBe(1.0);
  });

  it('returns 0.5 when true author is always rank 2', () => {
    const results = [
      makeResult('A', [{ author: 'B', score: 0.1 }, { author: 'A', score: 0.9 }]),
      makeResult('B', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),
    ];
    expect(computeMRR(results)).toBe(0.5);
  });

  it('averages mixed ranks correctly', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),  // rank 1 → 1/1
      makeResult('B', [{ author: 'A', score: 0.1 }, { author: 'B', score: 0.9 }]),  // rank 2 → 1/2
    ];
    expect(computeMRR(results)).toBeCloseTo(0.75, 5);
  });

  it('handles true author missing from rankings', () => {
    const results = [
      makeResult('A', [{ author: 'B', score: 0.5 }]),  // A not in rankings → 0
    ];
    expect(computeMRR(results)).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// computeF05u
// ---------------------------------------------------------------------------

describe('computeF05u', () => {
  it('returns null for empty input', () => {
    expect(computeF05u([])).toBeNull();
  });

  it('returns 1.0 for all correct, no non-answers', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.9 }]),
      makeResult('B', [{ author: 'B', score: 0.9 }]),
    ];
    expect(computeF05u(results)).toBeCloseTo(1.0, 5);
  });

  it('returns 0 for all wrong, no non-answers', () => {
    const results = [
      makeResult('A', [{ author: 'B', score: 0.9 }]),
      makeResult('B', [{ author: 'A', score: 0.9 }]),
    ];
    expect(computeF05u(results)).toBe(0);
  });

  it('credits non-answers (score=0.5 with threshold)', () => {
    const results = [
      makeResult('A', [{ author: 'A', score: 0.8 }], { verification_threshold: 0.5 }),
      makeResult('B', [{ author: 'B', score: 0.5 }], { verification_threshold: 0.5 }),  // non-answer
    ];
    const f05u = computeF05u(results);
    expect(f05u).not.toBeNull();
    // One correct answer, one non-answer (credited) → should be > 0
    expect(f05u!).toBeGreaterThan(0);
  });

  it('handles all non-answers', () => {
    const results = [
      makeResult('A', [{ author: 'X', score: 0.5 }], { verification_threshold: 0.5 }),
      makeResult('B', [{ author: 'Y', score: 0.5 }], { verification_threshold: 0.5 }),
    ];
    const f05u = computeF05u(results);
    expect(f05u).not.toBeNull();
    // nc=0, nu=2, nAnswered=0 → returns nc/n = 0
    expect(f05u!).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// computeBrier
// ---------------------------------------------------------------------------

describe('computeBrier', () => {
  it('returns null for empty input', () => {
    expect(computeBrier([])).toBeNull();
  });

  it('returns null when some results have empty rankings', () => {
    const results = [
      makeResult('A', []),
    ];
    expect(computeBrier(results)).toBeNull();
  });

  it('returns 1.0 for perfect confident predictions (higher_is_better)', () => {
    const results = [
      makeResult('A', [
        { author: 'A', score: 1.0 },
        { author: 'B', score: 0.0 },
      ], { lower_is_better: false }),
      makeResult('B', [
        { author: 'B', score: 1.0 },
        { author: 'A', score: 0.0 },
      ], { lower_is_better: false }),
    ];
    expect(computeBrier(results)).toBeCloseTo(1.0, 5);
  });

  it('returns value between 0 and 1', () => {
    const results = [
      makeResult('A', [
        { author: 'A', score: 0.6 },
        { author: 'B', score: 0.4 },
      ], { lower_is_better: false }),
      makeResult('B', [
        { author: 'A', score: 0.6 },
        { author: 'B', score: 0.4 },
      ], { lower_is_better: false }),
    ];
    const brier = computeBrier(results);
    expect(brier).not.toBeNull();
    expect(brier!).toBeGreaterThanOrEqual(0);
    expect(brier!).toBeLessThanOrEqual(1);
  });

  it('handles lower_is_better score inversion', () => {
    // Lower score = more confident, so score=0.1 → high confidence
    const results = [
      makeResult('A', [
        { author: 'A', score: 0.1 },
        { author: 'B', score: 0.9 },
      ]),
    ];
    const brier = computeBrier(results);
    expect(brier).not.toBeNull();
    // Correct prediction with high confidence → Brier close to 1
    expect(brier!).toBeGreaterThan(0.5);
  });
});
