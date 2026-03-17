import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { pipelineApi } from '../api/pipeline';
import { corporaApi } from '../api/corpora';
import { useExperimentStore } from '../store/experimentStore';
import { useCreateExperiment } from '../hooks/useExperiment';
import type { ComponentInfo, ComponentSpec, ParamInfo, CorpusResponse } from '../types';
import s from './ExperimentBuilderPage.module.css';

// Re-export the value type from ComponentSpec to avoid explicit `any` in signatures
type ParamValue = ComponentSpec['params'][string];

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STEPS = [
  'Name & Corpora',
  'Canonicizers',
  'Event Drivers',
  'Event Cullers',
  'Distance Function',
  'Analysis Method',
  'Review & Submit',
] as const;

// ---------------------------------------------------------------------------
// ParameterEditor
// ---------------------------------------------------------------------------

function ParameterEditor({
  params,
  values,
  onChange,
}: {
  params: ParamInfo[];
  values: ComponentSpec['params'];
  onChange: (name: string, value: ParamValue) => void;
}) {
  return (
    <div className={s.paramFields}>
      {params.map((p) => {
        const val = values[p.name] ?? p.default ?? '';

        if (p.choices && p.choices.length > 0) {
          return (
            <div key={p.name}>
              <label className={s.paramLabel}>
                {p.name}
                {p.description && (
                  <span className={s.paramHint}>
                    - {p.description}
                  </span>
                )}
              </label>
              <select
                value={String(val)}
                onChange={(e) => onChange(p.name, e.target.value)}
                className={s.paramInput}
              >
                {p.choices.map((c) => (
                  <option key={String(c)} value={String(c)}>
                    {String(c)}
                  </option>
                ))}
              </select>
            </div>
          );
        }

        const isNumeric = p.type === 'int' || p.type === 'float';
        return (
          <div key={p.name}>
            <label className={s.paramLabel}>
              {p.name}
              {p.description && (
                <span className={s.paramHint}>
                  - {p.description}
                </span>
              )}
            </label>
            <input
              type={isNumeric ? 'number' : 'text'}
              value={val}
              min={p.min_value ?? undefined}
              max={p.max_value ?? undefined}
              step={p.type === 'float' ? 'any' : undefined}
              onChange={(e) => {
                const raw = e.target.value;
                if (isNumeric) {
                  onChange(p.name, raw === '' ? '' : p.type === 'int' ? parseInt(raw, 10) : parseFloat(raw));
                } else {
                  onChange(p.name, raw);
                }
              }}
              className={s.paramInput}
            />
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ComponentSelector (multi-select with cards)
// ---------------------------------------------------------------------------

function ComponentSelector({
  components,
  selected,
  onChange,
  isLoading,
  multiSelect,
}: {
  components: ComponentInfo[];
  selected: ComponentSpec[];
  onChange: (specs: ComponentSpec[]) => void;
  isLoading: boolean;
  multiSelect: boolean;
}) {
  if (isLoading) {
    return <p className={s.stepDesc}>Loading components...</p>;
  }

  if (components.length === 0) {
    return <p className={s.stepDesc}>No components available.</p>;
  }

  const selectedMap = new Map(selected.map((s) => [s.name, s]));

  const toggle = (comp: ComponentInfo) => {
    if (multiSelect) {
      if (selectedMap.has(comp.name)) {
        onChange(selected.filter((s) => s.name !== comp.name));
      } else {
        const defaults: ComponentSpec['params'] = {};
        if (comp.params) {
          for (const p of comp.params) {
            if (p.default !== null && p.default !== undefined) {
              defaults[p.name] = p.default;
            }
          }
        }
        onChange([...selected, { name: comp.name, params: defaults }]);
      }
    } else {
      // single select
      if (selectedMap.has(comp.name)) {
        // already selected - deselect not allowed for required single-select
        return;
      }
      const defaults: ComponentSpec['params'] = {};
      if (comp.params) {
        for (const p of comp.params) {
          if (p.default !== null && p.default !== undefined) {
            defaults[p.name] = p.default;
          }
        }
      }
      onChange([{ name: comp.name, params: defaults }]);
    }
  };

  const updateParams = (compName: string, paramName: string, value: ParamValue) => {
    onChange(
      selected.map((s) =>
        s.name === compName ? { ...s, params: { ...s.params, [paramName]: value } } : s,
      ),
    );
  };

  return (
    <div className={s.componentGrid}>
      {components.map((comp) => {
        const isSelected = selectedMap.has(comp.name);
        const spec = selectedMap.get(comp.name);
        return (
          <div
            key={comp.name}
            onClick={() => toggle(comp)}
            className={`${s.componentCard} ${isSelected ? s.componentCardSelected : ''}`}
          >
            <div className={s.componentHeader}>
              <div>
                <div className={s.componentName}>
                  {comp.display_name}
                </div>
                <div className={s.componentSlug}>
                  {comp.name}
                </div>
              </div>
              <div
                className={`${multiSelect ? s.checkbox : s.radio} ${isSelected ? s.checkboxSelected : ''}`}
              >
                {isSelected && (
                  <span className={s.checkmark}>
                    {multiSelect ? '\u2713' : '\u25CF'}
                  </span>
                )}
              </div>
            </div>
            {comp.description && (
              <p className={s.componentDesc}>
                {comp.description}
              </p>
            )}
            {isSelected && comp.params && comp.params.length > 0 && spec && (
              <div onClick={(e) => e.stopPropagation()}>
                <ParameterEditor
                  params={comp.params}
                  values={spec.params}
                  onChange={(paramName, value) => updateParams(comp.name, paramName, value)}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 1: Name & Corpora
// ---------------------------------------------------------------------------

function StepNameCorpora({ corpora, isLoading }: { corpora: CorpusResponse[]; isLoading: boolean }) {
  const name = useExperimentStore((s) => s.name);
  const setName = useExperimentStore((s) => s.setName);
  const knownCorpusIds = useExperimentStore((s) => s.knownCorpusIds);
  const setKnownCorpusIds = useExperimentStore((s) => s.setKnownCorpusIds);
  const unknownCorpusIds = useExperimentStore((s) => s.unknownCorpusIds);
  const setUnknownCorpusIds = useExperimentStore((s) => s.setUnknownCorpusIds);

  const toggleCorpus = (ids: number[], setIds: (ids: number[]) => void, id: number) => {
    if (ids.includes(id)) {
      setIds(ids.filter((i) => i !== id));
    } else {
      setIds([...ids, id]);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <label className={s.paramLabel} style={{ display: 'block', fontSize: '0.9rem' }}>
          Experiment Name
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter experiment name"
          className={`${s.paramInput} ${s.nameInput}`}
        />
      </div>

      {isLoading && <p className={s.stepDesc}>Loading corpora...</p>}

      {!isLoading && corpora.length === 0 && (
        <p className={s.stepDesc}>
          No corpora available. Create corpora before building an experiment.
        </p>
      )}

      {!isLoading && corpora.length > 0 && (
        <div className={s.corporaGrid}>
          {/* Known corpora */}
          <div>
            <h3 style={{ marginBottom: '0.5rem' }}>
              Known Corpora
              <span className={s.corpusCount} style={{ fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (training data with known authors)
              </span>
            </h3>
            <div className={s.corporaList}>
              {corpora.map((c) => (
                <label
                  key={c.id}
                  className={s.corpusLabel}
                >
                  <input
                    type="checkbox"
                    checked={knownCorpusIds.includes(c.id)}
                    onChange={() => toggleCorpus(knownCorpusIds, setKnownCorpusIds, c.id)}
                    style={{ accentColor: 'var(--accent)' }}
                  />
                  <span>{c.name}</span>
                  <span className={s.corpusCount}>
                    {c.document_count} doc{c.document_count !== 1 ? 's' : ''}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Unknown corpora */}
          <div>
            <h3 style={{ marginBottom: '0.5rem' }}>
              Unknown Corpora
              <span className={s.corpusCount} style={{ fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (documents to attribute)
              </span>
            </h3>
            <div className={s.corporaList}>
              {corpora.map((c) => (
                <label
                  key={c.id}
                  className={s.corpusLabel}
                >
                  <input
                    type="checkbox"
                    checked={unknownCorpusIds.includes(c.id)}
                    onChange={() => toggleCorpus(unknownCorpusIds, setUnknownCorpusIds, c.id)}
                    style={{ accentColor: 'var(--accent)' }}
                  />
                  <span>{c.name}</span>
                  <span className={s.corpusCount}>
                    {c.document_count} doc{c.document_count !== 1 ? 's' : ''}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 7: Review & Submit
// ---------------------------------------------------------------------------

function StepReview({
  corpora,
  allCanonicizers,
  allEventDrivers,
  allEventCullers,
  allDistanceFunctions,
  allAnalysisMethods,
  numericMode,
}: {
  corpora: CorpusResponse[];
  allCanonicizers: ComponentInfo[];
  allEventDrivers: ComponentInfo[];
  allEventCullers: ComponentInfo[];
  allDistanceFunctions: ComponentInfo[];
  allAnalysisMethods: ComponentInfo[];
  numericMode: boolean;
}) {
  const store = useExperimentStore();
  const corporaMap = new Map(corpora.map((c) => [c.id, c]));

  const findDisplayName = (list: ComponentInfo[], name: string) => {
    const item = list.find((c) => c.name === name);
    return item ? item.display_name : name;
  };

  return (
    <div>
      <div className="section-panel">
        <div className="section-label">Experiment Name</div>
        <div style={{ fontWeight: 600, fontSize: '1.05rem' }}>{store.name}</div>
      </div>

      <div className={s.reviewGrid}>
        <div className="section-panel">
          <div className="section-label">Known Corpora</div>
          {store.knownCorpusIds.length === 0 ? (
            <span className={s.stepDesc}>None selected</span>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {store.knownCorpusIds.map((id) => (
                <li key={id} style={{ fontSize: '0.9rem' }}>
                  {corporaMap.get(id)?.name ?? `Corpus #${id}`}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="section-panel">
          <div className="section-label">Unknown Corpora</div>
          {store.unknownCorpusIds.length === 0 ? (
            <span className={s.stepDesc}>None selected</span>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {store.unknownCorpusIds.map((id) => (
                <li key={id} style={{ fontSize: '0.9rem' }}>
                  {corporaMap.get(id)?.name ?? `Corpus #${id}`}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="section-panel">
        <div className="section-label">Canonicizers</div>
        {store.canonicizers.length === 0 ? (
          <span className={s.stepDesc}>None</span>
        ) : (
          <div className={s.reviewChips}>
            {store.canonicizers.map((c) => (
              <span key={c.name} className={s.reviewChip}>
                {findDisplayName(allCanonicizers, c.name)}
                {Object.keys(c.params).length > 0 && (
                  <span className={s.reviewChipParams}>
                    ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="section-panel">
        <div className="section-label">Event Drivers</div>
        <div className={s.reviewChips}>
          {store.eventDrivers.map((c) => (
            <span key={c.name} className={s.reviewChip}>
              {findDisplayName(allEventDrivers, c.name)}
              {Object.keys(c.params).length > 0 && (
                <span className={s.reviewChipParams}>
                  ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                </span>
              )}
            </span>
          ))}
        </div>
      </div>

      <div className="section-panel">
        <div className="section-label">Event Cullers</div>
        {numericMode ? (
          <span className={s.stepDesc}>N/A (embedding mode)</span>
        ) : store.eventCullers.length === 0 ? (
          <span className={s.stepDesc}>None</span>
        ) : (
          <div className={s.reviewChips}>
            {store.eventCullers.map((c) => (
              <span key={c.name} className={s.reviewChip}>
                {findDisplayName(allEventCullers, c.name)}
                {Object.keys(c.params).length > 0 && (
                  <span className={s.reviewChipParams}>
                    ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className={s.reviewGrid}>
        <div className="section-panel">
          <div className="section-label">Distance Function</div>
          {numericMode ? (
            <span className={s.stepDesc}>N/A (embedding mode)</span>
          ) : (
            <>
              <span style={{ fontSize: '0.9rem' }}>
                {store.distanceFunction
                  ? findDisplayName(allDistanceFunctions, store.distanceFunction.name)
                  : 'None'}
              </span>
              {store.distanceFunction && Object.keys(store.distanceFunction.params).length > 0 && (
                <span className={s.reviewChipParams}>
                  ({Object.entries(store.distanceFunction.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                </span>
              )}
            </>
          )}
        </div>
        <div className="section-panel">
          <div className="section-label">Analysis Method</div>
          <span style={{ fontSize: '0.9rem' }}>
            {findDisplayName(allAnalysisMethods, store.analysisMethod.name)}
          </span>
          {Object.keys(store.analysisMethod.params).length > 0 && (
            <span className={s.reviewChipParams}>
              ({Object.entries(store.analysisMethod.params).map(([k, v]) => `${k}=${v}`).join(', ')})
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ExperimentBuilderPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const store = useExperimentStore();
  const createExperiment = useCreateExperiment();

  // ----- data queries ------------------------------------------------------

  const { data: corpora = [], isLoading: corporaLoading } = useQuery({
    queryKey: ['corpora'],
    queryFn: corporaApi.list,
  });

  const { data: canonicizers = [], isLoading: canonicizersLoading } = useQuery({
    queryKey: ['pipeline', 'canonicizers'],
    queryFn: pipelineApi.getCanonicizers,
  });

  const { data: eventDrivers = [], isLoading: eventDriversLoading } = useQuery({
    queryKey: ['pipeline', 'event-drivers'],
    queryFn: pipelineApi.getEventDrivers,
  });

  const { data: eventCullers = [], isLoading: eventCullersLoading } = useQuery({
    queryKey: ['pipeline', 'event-cullers'],
    queryFn: pipelineApi.getEventCullers,
  });

  const { data: distanceFunctions = [], isLoading: distanceFunctionsLoading } = useQuery({
    queryKey: ['pipeline', 'distance-functions'],
    queryFn: pipelineApi.getDistanceFunctions,
  });

  const { data: analysisMethods = [], isLoading: analysisMethodsLoading } = useQuery({
    queryKey: ['pipeline', 'analysis-methods'],
    queryFn: pipelineApi.getAnalysisMethods,
  });

  // ----- numeric mode detection ---------------------------------------------

  // Numeric mode is active when any selected event driver is a numeric
  // (embedding) driver. In this mode, cullers and distance functions are
  // not applicable and analysis methods must be sklearn-based.
  const numericMode = store.eventDrivers.some((d) => {
    const info = eventDrivers.find((ed) => ed.name === d.name);
    return info?.numeric === true;
  });

  // ----- validation --------------------------------------------------------

  const canProceed = (): boolean => {
    switch (step) {
      case 0:
        return (
          store.name.trim().length > 0 &&
          store.knownCorpusIds.length > 0 &&
          store.unknownCorpusIds.length > 0
        );
      case 1:
        return true; // optional
      case 2:
        return store.eventDrivers.length > 0;
      case 3:
        return true; // optional (or skipped in numeric mode)
      case 4:
        return numericMode || store.distanceFunction !== null;
      case 5:
        return store.analysisMethod.name.length > 0;
      case 6:
        return true;
      default:
        return false;
    }
  };

  // ----- submit ------------------------------------------------------------

  const handleSubmit = () => {
    setSubmitError(null);
    const config = store.getConfig();
    // In numeric mode, clear incompatible selections
    if (numericMode) {
      config.event_cullers = [];
      config.distance_function = null;
    }
    createExperiment.mutate(
      {
        name: store.name,
        config,
        known_corpus_ids: store.knownCorpusIds,
        unknown_corpus_ids: store.unknownCorpusIds,
      },
      {
        onSuccess: (experiment) => {
          navigate(`/experiments/${experiment.id}/results`);
        },
        onError: (err: Error) => {
          setSubmitError(err.message || 'Failed to create experiment.');
        },
      },
    );
  };

  // ----- render steps ------------------------------------------------------

  const renderStep = () => {
    switch (step) {
      case 0:
        return <StepNameCorpora corpora={corpora} isLoading={corporaLoading} />;
      case 1:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Canonicizers</h2>
            <p className={s.stepDesc}>
              Text preprocessing steps. Optional - select any that apply.
            </p>
            <ComponentSelector
              components={canonicizers}
              selected={store.canonicizers}
              onChange={store.setCanonicizers}
              isLoading={canonicizersLoading}
              multiSelect
            />
          </div>
        );
      case 2:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Event Drivers</h2>
            <p className={s.stepDesc}>
              Methods for extracting features from text. At least one is required.
            </p>
            <ComponentSelector
              components={eventDrivers}
              selected={store.eventDrivers}
              onChange={store.setEventDrivers}
              isLoading={eventDriversLoading}
              multiSelect
            />
          </div>
        );
      case 3:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Event Cullers</h2>
            {numericMode ? (
              <p className={s.stepDesc}>
                Event cullers are not applicable with embedding-based event drivers.
                This step will be skipped.
              </p>
            ) : (
              <>
                <p className={s.stepDesc}>
                  Filter extracted events. Optional.
                </p>
                <ComponentSelector
                  components={eventCullers}
                  selected={store.eventCullers}
                  onChange={store.setEventCullers}
                  isLoading={eventCullersLoading}
                  multiSelect
                />
              </>
            )}
          </div>
        );
      case 4:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Distance Function</h2>
            {numericMode ? (
              <p className={s.stepDesc}>
                Distance functions are not applicable with embedding-based event drivers.
                The sklearn analysis method handles similarity internally. This step will be skipped.
              </p>
            ) : (
              <>
                <p className={s.stepDesc}>
                  How to measure distance between event distributions. Select one.
                </p>
                <ComponentSelector
                  components={distanceFunctions}
                  selected={store.distanceFunction ? [store.distanceFunction] : []}
                  onChange={(specs) => store.setDistanceFunction(specs[0] ?? null)}
                  isLoading={distanceFunctionsLoading}
                  multiSelect={false}
                />
              </>
            )}
          </div>
        );
      case 5: {
        const filteredMethods = numericMode
          ? analysisMethods.filter((m) => m.numeric === true)
          : analysisMethods;
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Analysis Method</h2>
            <p className={s.stepDesc}>
              {numericMode
                ? 'Select a classifier for the embedding vectors. Only sklearn-based methods are compatible with embeddings.'
                : 'The method used to determine authorship attribution. Select one.'}
            </p>
            <ComponentSelector
              components={filteredMethods}
              selected={[store.analysisMethod]}
              onChange={(specs) => {
                if (specs.length > 0) store.setAnalysisMethod(specs[0]);
              }}
              isLoading={analysisMethodsLoading}
              multiSelect={false}
            />
          </div>
        );
      }
      case 6:
        return (
          <div>
            <h2 style={{ marginBottom: '1rem' }}>Review & Submit</h2>
            <StepReview
              corpora={corpora}
              allCanonicizers={canonicizers}
              allEventDrivers={eventDrivers}
              allEventCullers={eventCullers}
              allDistanceFunctions={distanceFunctions}
              allAnalysisMethods={analysisMethods}
              numericMode={numericMode}
            />
            {submitError && (
              <div className={s.errorBox}>
                {submitError}
              </div>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  // ----- render main -------------------------------------------------------

  return (
    <div>
      <h1>New Experiment</h1>

      {/* Step indicators */}
      <div className={s.stepIndicatorRow}>
        {STEPS.map((label, i) => {
          const isActive = i === step;
          const isCompleted = i < step;
          const isClickable = i <= step;
          return (
            <button
              key={i}
              onClick={() => {
                // Allow clicking on completed steps or current step
                if (i <= step) setStep(i);
              }}
              className={`${s.stepBtn} ${isActive ? s.stepBtnActive : ''} ${isCompleted ? s.stepBtnCompleted : ''} ${isClickable ? s.stepBtnClickable : ''}`}
            >
              <span
                className={`${s.stepNumber} ${isActive ? s.stepNumberActive : ''} ${isCompleted ? s.stepNumberCompleted : ''}`}
              >
                {isCompleted ? '\u2713' : i + 1}
              </span>
              {label}
            </button>
          );
        })}
      </div>

      {/* Step content */}
      <div className="card">{renderStep()}</div>

      {/* Navigation buttons */}
      <div className={s.navRow}>
        <button
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
          style={{ visibility: step === 0 ? 'hidden' : 'visible' }}
        >
          Back
        </button>

        {step < STEPS.length - 1 ? (
          <button
            className="primary"
            onClick={() => setStep((s) => s + 1)}
            disabled={!canProceed()}
          >
            Next
          </button>
        ) : (
          <button
            className="primary"
            onClick={handleSubmit}
            disabled={createExperiment.isPending}
          >
            {createExperiment.isPending ? 'Submitting...' : 'Submit Experiment'}
          </button>
        )}
      </div>
    </div>
  );
}
