import type { CSSProperties } from 'react';

export default function ProgressBar({ progress }: { progress: number }) {
  const pct = Math.min(Math.max(progress, 0), 100);
  return (
    <div className="progress-bar-wrap">
      <div className="progress-bar__meta">
        <span className="progress-bar__label">Progress</span>
        <span className="progress-bar__value">{Math.round(pct)}%</span>
      </div>
      <div
        className="progress-bar"
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Experiment progress"
      >
        <div
          className="progress-bar__fill"
          style={{ '--progress-scale': pct / 100 } as CSSProperties}
        />
      </div>
    </div>
  );
}
