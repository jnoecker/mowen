import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../api/documents';
import { corporaApi } from '../api/corpora';
import { experimentsApi } from '../api/experiments';
import StatusBadge from '../components/StatusBadge';
import s from './DashboardPage.module.css';

function ShelfMetric({
  label,
  value,
  note,
  isLoading,
}: {
  label: string;
  value: number;
  note: string;
  isLoading: boolean;
}) {
  return (
    <div className={s.metricTile}>
      <div className={s.metricValue}>{isLoading ? '-' : value}</div>
      <div className={s.metricLabel}>{label}</div>
      <div className={s.metricNote}>{note}</div>
    </div>
  );
}

function WorkflowCard({
  number,
  title,
  description,
  actionLabel,
  onAction,
  complete,
}: {
  number: string;
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
  complete: boolean;
}) {
  return (
    <article className={s.workflowCard}>
      <div className={s.workflowTop}>
        <div className={s.workflowNumber}>{number}</div>
        <div className={s.workflowStatus}>{complete ? 'ready' : 'to do'}</div>
      </div>
      <h3 className={s.workflowTitle}>{title}</h3>
      <p className={s.workflowText}>{description}</p>
      <button onClick={onAction}>{actionLabel}</button>
    </article>
  );
}

function GettingStarted({ onNavigate }: { onNavigate: (path: string) => void }) {
  return (
    <div className={s.page}>
      <section className={s.heroGrid}>
        <div className={`card ${s.heroPanel}`}>
          <p className={s.eyebrow}>Scriptorium</p>
          <h1 className={s.heroTitle}>Assemble your first inquiry</h1>
          <p className={s.heroLead}>
            mowen is strongest when it feels like a scholar&apos;s bench: set aside reference texts,
            bring forward a questioned document, and test a method from the literature without
            having to think like an ML engineer.
          </p>
          <div className={s.heroActions}>
            <button className="primary" onClick={() => onNavigate('/corpora')}>
              Import sample corpus
            </button>
            <button onClick={() => onNavigate('/documents')}>Upload your own texts</button>
          </div>
          <p className={s.heroQuote}>
            Build from a known precedent, compare textual habits, then read the evidence side by side.
          </p>
        </div>

        <aside className={`card ${s.notePanel}`}>
          <p className={s.noteLabel}>First session</p>
          <h2 className={s.noteTitle}>Start with a benchmark, then revise from there</h2>
          <p className={s.noteText}>
            If you are new to the tool, importing a sample corpus is the quickest way to see a full
            stylometric workflow before you bring in your own archive.
          </p>
          <button className="primary" onClick={() => onNavigate('/corpora')}>
            Open corpora desk
          </button>
          <p className={s.noteMeta}>You can switch to your own documents at any point.</p>
        </aside>
      </section>

      <section className={s.deskGrid}>
        <div className={`card ${s.workflowPanel} ${s.fullWidth}`}>
          <div className={s.sectionHeader}>
            <div>
              <p className={s.sectionLabel}>Research path</p>
              <h2 className={s.sectionTitle}>A calm way to begin</h2>
            </div>
          </div>

          <div className={s.workflowGrid}>
            <WorkflowCard
              number="01"
              title="Gather the texts"
              description="Upload source documents or import a sample corpus so the workspace has something to study."
              actionLabel="Go to documents"
              onAction={() => onNavigate('/documents')}
              complete={false}
            />
            <WorkflowCard
              number="02"
              title="Arrange the shelves"
              description="Separate known-author corpora from questioned texts so the experiment has a clear frame."
              actionLabel="Go to corpora"
              onAction={() => onNavigate('/corpora')}
              complete={false}
            />
            <WorkflowCard
              number="03"
              title="Test a method"
              description="Start from a literature-backed preset, then adjust the parts that matter for your question."
              actionLabel="New experiment"
              onAction={() => onNavigate('/experiments/new')}
              complete={false}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

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

  if (isEmpty) {
    return <GettingStarted onNavigate={navigate} />;
  }

  const recentExperiments = [...experiments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  const latestExperiment = recentExperiments[0];

  const nextStep = (() => {
    if (documents.length === 0) {
      return {
        title: 'Begin by gathering source texts',
        text: 'The workspace still needs documents before you can build a meaningful comparison.',
        actionLabel: 'Upload documents',
        path: '/documents',
      };
    }

    if (corpora.length === 0) {
      return {
        title: 'Arrange the archive into corpora',
        text: 'Group known authors and questioned texts into separate shelves so an experiment has a clear frame.',
        actionLabel: 'Organize corpora',
        path: '/corpora',
      };
    }

    if (experiments.length === 0) {
      return {
        title: 'Compose the first experiment',
        text: 'You have texts and corpora ready. Start from a published method, then tune only the details your question requires.',
        actionLabel: 'New experiment',
        path: '/experiments/new',
      };
    }

    return {
      title: 'Open the latest results and compare the voices',
      text: 'Return to your most recent inquiry or start a new one with a different methodological angle.',
      actionLabel: latestExperiment ? 'View latest results' : 'New experiment',
      path: latestExperiment ? `/experiments/${latestExperiment.id}/results` : '/experiments/new',
    };
  })();

  return (
    <div className={s.page}>
      <section className={s.heroGrid}>
        <div className={`card ${s.heroPanel}`}>
          <p className={s.eyebrow}>Scholar&apos;s Desk</p>
          <h1 className={s.heroTitle}>Return to the reading bench</h1>
          <p className={s.heroLead}>
            Keep the focus on texts, corpora, and evidence. The pipeline remains configurable, but
            the work should still feel like comparative reading rather than administering a system.
          </p>
          <div className={s.heroActions}>
            <button className="primary" onClick={() => navigate('/experiments/new')}>
              New experiment
            </button>
            <button onClick={() => navigate('/documents')}>Open documents</button>
          </div>

          <div className={s.metricStrip}>
            <ShelfMetric
              label="Documents"
              value={documents.length}
              note="Texts currently on the desk"
              isLoading={docsLoading}
            />
            <ShelfMetric
              label="Corpora"
              value={corpora.length}
              note="Reference and questioned shelves"
              isLoading={corporaLoading}
            />
            <ShelfMetric
              label="Experiments"
              value={experiments.length}
              note="Completed or in-progress inquiries"
              isLoading={experimentsLoading}
            />
          </div>
        </div>

        <aside className={`card ${s.notePanel}`}>
          <p className={s.noteLabel}>Bench note</p>
          <h2 className={s.noteTitle}>{nextStep.title}</h2>
          <p className={s.noteText}>{nextStep.text}</p>
          <button className="primary" onClick={() => navigate(nextStep.path)}>
            {nextStep.actionLabel}
          </button>
          {latestExperiment && (
            <p className={s.noteMeta}>
              Most recent inquiry: <span>{latestExperiment.name}</span>
            </p>
          )}
        </aside>
      </section>

      <section className={s.deskGrid}>
        <div className={`card ${s.recentPanel}`}>
          <div className={s.sectionHeader}>
            <div>
              <p className={s.sectionLabel}>Recent inquiries</p>
              <h2 className={s.sectionTitle}>Open a recent verdict</h2>
            </div>
            {experiments.length > 0 && (
              <button onClick={() => navigate('/experiments')}>View all experiments</button>
            )}
          </div>

          {experimentsLoading && <p className={s.emptyNote}>Loading experiments...</p>}

          {!experimentsLoading && experiments.length === 0 && (
            <p className={s.emptyNote}>
              No experiments yet. Once you have corpora arranged, start with a preset and compare how
              different methods read the same texts.
            </p>
          )}

          {!experimentsLoading && recentExperiments.length > 0 && (
            <div className={s.tableWrap}>
              <table>
                <caption className="sr-only">Recent experiments</caption>
                <thead>
                  <tr>
                    <th>Inquiry</th>
                    <th>Status</th>
                    <th>Opened</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recentExperiments.map((exp) => (
                    <tr key={exp.id}>
                      <td className={s.nameCell}>{exp.name}</td>
                      <td>
                        <StatusBadge status={exp.status} />
                      </td>
                      <td className={s.dateCell}>
                        {new Date(exp.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <Link to={`/experiments/${exp.id}/results`} className="text-sm">
                          View results
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <aside className={`card ${s.workflowPanel}`}>
          <div className={s.sectionHeader}>
            <div>
              <p className={s.sectionLabel}>Research path</p>
              <h2 className={s.sectionTitle}>Keep the workflow legible</h2>
            </div>
          </div>

          <div className={s.workflowStack}>
            <WorkflowCard
              number="01"
              title="Gather texts"
              description="Bring in source material whenever the desk needs more evidence."
              actionLabel="Open documents"
              onAction={() => navigate('/documents')}
              complete={documents.length > 0}
            />
            <WorkflowCard
              number="02"
              title="Arrange corpora"
              description="Keep reference corpora and questioned texts clearly separated."
              actionLabel="Open corpora"
              onAction={() => navigate('/corpora')}
              complete={corpora.length > 0}
            />
            <WorkflowCard
              number="03"
              title="Compare methods"
              description="Run multiple experiments against the same texts to see where the evidence converges."
              actionLabel="Compose experiment"
              onAction={() => navigate('/experiments/new')}
              complete={experiments.length > 0}
            />
          </div>
        </aside>
      </section>
    </div>
  );
}
