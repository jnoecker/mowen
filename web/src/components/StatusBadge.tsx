import type { ExperimentResponse } from '../types';

const statusClasses: Record<string, string> = {
  pending: 'badge badge--pending',
  running: 'badge badge--running',
  completed: 'badge badge--completed',
  failed: 'badge badge--failed',
};

const statusIcons: Record<string, string> = {
  pending: '\u25CB',   // ○
  running: '\u25D4',   // ◔
  completed: '\u2713', // ✓
  failed: '\u2717',    // ✗
};

export default function StatusBadge({ status }: { status: ExperimentResponse['status'] }) {
  return (
    <span className={statusClasses[status] ?? statusClasses.pending}>
      <span aria-hidden="true">{statusIcons[status] ?? statusIcons.pending} </span>
      {status}
    </span>
  );
}
