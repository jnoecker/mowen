import type { ExperimentResponse } from '../types';

const statusClasses: Record<string, string> = {
  pending: 'badge badge--pending',
  running: 'badge badge--running',
  completed: 'badge badge--completed',
  failed: 'badge badge--failed',
};

export default function StatusBadge({ status }: { status: ExperimentResponse['status'] }) {
  return (
    <span className={statusClasses[status] ?? statusClasses.pending}>
      {status}
    </span>
  );
}
