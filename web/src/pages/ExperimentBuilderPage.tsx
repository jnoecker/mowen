import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { pipelineApi } from '../api/pipeline';
import { corporaApi } from '../api/corpora';
import { useExperimentStore } from '../store/experimentStore';
import { useCreateExperiment } from '../hooks/useExperiment';
import type { ComponentInfo, ComponentSpec, ParamInfo, CorpusResponse } from '../types';

// Re-export the value type from ComponentSpec to avoid explicit `any` in signatures
type ParamValue = ComponentSpec['params'][string];

// ---------------------------------------------------------------------------
// Constants & Styles
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

const cardStyle: React.CSSProperties = {
  background: '#1a1a2e',
  border: '1px solid #2a2a4a',
  borderRadius: '8px',
  padding: '1.25rem',
  marginBottom: '1rem',
};

const stepIndicatorRow: React.CSSProperties = {
  display: 'flex',
  gap: '0.25rem',
  marginBottom: '2rem',
  flexWrap: 'wrap',
};

const navRow: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  marginTop: '2rem',
  paddingTop: '1rem',
  borderTop: '1px solid #2a2a4a',
};

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
      {params.map((p) => {
        const val = values[p.name] ?? p.default ?? '';

        if (p.choices && p.choices.length > 0) {
          return (
            <div key={p.name}>
              <label style={{ fontSize: '0.8rem', color: '#8888aa', marginBottom: '0.15rem' }}>
                {p.name}
                {p.description && (
                  <span style={{ marginLeft: '0.5rem', fontWeight: 'normal', opacity: 0.7 }}>
                    - {p.description}
                  </span>
                )}
              </label>
              <select
                value={String(val)}
                onChange={(e) => onChange(p.name, e.target.value)}
                style={{
                  width: '100%',
                  background: '#16213e',
                  border: '1px solid #2a2a4a',
                  borderRadius: '6px',
                  color: '#e0e0e0',
                  padding: '0.4rem 0.6rem',
                  fontSize: '0.85rem',
                }}
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
            <label style={{ fontSize: '0.8rem', color: '#8888aa', marginBottom: '0.15rem' }}>
              {p.name}
              {p.description && (
                <span style={{ marginLeft: '0.5rem', fontWeight: 'normal', opacity: 0.7 }}>
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
              style={{
                width: '100%',
                background: '#16213e',
                border: '1px solid #2a2a4a',
                borderRadius: '6px',
                color: '#e0e0e0',
                padding: '0.4rem 0.6rem',
                fontSize: '0.85rem',
              }}
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
    return <p style={{ color: '#8888aa' }}>Loading components...</p>;
  }

  if (components.length === 0) {
    return <p style={{ color: '#8888aa' }}>No components available.</p>;
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
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '0.75rem' }}>
      {components.map((comp) => {
        const isSelected = selectedMap.has(comp.name);
        const spec = selectedMap.get(comp.name);
        return (
          <div
            key={comp.name}
            onClick={() => toggle(comp)}
            style={{
              background: '#1a1a2e',
              border: isSelected ? '2px solid #7c8cf8' : '1px solid #2a2a4a',
              borderRadius: '8px',
              padding: '1rem',
              cursor: 'pointer',
              transition: 'border-color 0.15s, box-shadow 0.15s',
              boxShadow: isSelected ? '0 0 8px rgba(124, 140, 248, 0.2)' : 'none',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: '#e0e0e0', fontSize: '0.95rem' }}>
                  {comp.display_name}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#8888aa', fontFamily: 'monospace' }}>
                  {comp.name}
                </div>
              </div>
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: multiSelect ? '4px' : '50%',
                  border: isSelected ? '2px solid #7c8cf8' : '2px solid #2a2a4a',
                  background: isSelected ? '#7c8cf8' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {isSelected && (
                  <span style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 'bold' }}>
                    {multiSelect ? '\u2713' : '\u25CF'}
                  </span>
                )}
              </div>
            </div>
            {comp.description && (
              <p style={{ fontSize: '0.82rem', color: '#8888aa', marginTop: '0.4rem', lineHeight: 1.4 }}>
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
        <label style={{ fontSize: '0.9rem', color: '#8888aa', marginBottom: '0.35rem', display: 'block' }}>
          Experiment Name
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter experiment name"
          style={{
            width: '100%',
            maxWidth: '500px',
            background: '#16213e',
            border: '1px solid #2a2a4a',
            borderRadius: '6px',
            color: '#e0e0e0',
            padding: '0.5rem 0.75rem',
            fontSize: '0.9rem',
          }}
        />
      </div>

      {isLoading && <p style={{ color: '#8888aa' }}>Loading corpora...</p>}

      {!isLoading && corpora.length === 0 && (
        <p style={{ color: '#8888aa' }}>
          No corpora available. Create corpora before building an experiment.
        </p>
      )}

      {!isLoading && corpora.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          {/* Known corpora */}
          <div>
            <h3 style={{ color: '#e0e0e0', marginBottom: '0.5rem' }}>
              Known Corpora
              <span style={{ fontSize: '0.8rem', color: '#8888aa', fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (training data with known authors)
              </span>
            </h3>
            <div
              style={{
                background: '#16213e',
                border: '1px solid #2a2a4a',
                borderRadius: '6px',
                padding: '0.75rem',
                maxHeight: '300px',
                overflowY: 'auto',
              }}
            >
              {corpora.map((c) => (
                <label
                  key={c.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.25rem',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    color: '#e0e0e0',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={knownCorpusIds.includes(c.id)}
                    onChange={() => toggleCorpus(knownCorpusIds, setKnownCorpusIds, c.id)}
                    style={{ accentColor: '#7c8cf8' }}
                  />
                  <span>{c.name}</span>
                  <span style={{ fontSize: '0.75rem', color: '#8888aa', marginLeft: 'auto' }}>
                    {c.document_count} doc{c.document_count !== 1 ? 's' : ''}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Unknown corpora */}
          <div>
            <h3 style={{ color: '#e0e0e0', marginBottom: '0.5rem' }}>
              Unknown Corpora
              <span style={{ fontSize: '0.8rem', color: '#8888aa', fontWeight: 'normal', marginLeft: '0.5rem' }}>
                (documents to attribute)
              </span>
            </h3>
            <div
              style={{
                background: '#16213e',
                border: '1px solid #2a2a4a',
                borderRadius: '6px',
                padding: '0.75rem',
                maxHeight: '300px',
                overflowY: 'auto',
              }}
            >
              {corpora.map((c) => (
                <label
                  key={c.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.4rem 0.25rem',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    color: '#e0e0e0',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={unknownCorpusIds.includes(c.id)}
                    onChange={() => toggleCorpus(unknownCorpusIds, setUnknownCorpusIds, c.id)}
                    style={{ accentColor: '#7c8cf8' }}
                  />
                  <span>{c.name}</span>
                  <span style={{ fontSize: '0.75rem', color: '#8888aa', marginLeft: 'auto' }}>
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
}: {
  corpora: CorpusResponse[];
  allCanonicizers: ComponentInfo[];
  allEventDrivers: ComponentInfo[];
  allEventCullers: ComponentInfo[];
  allDistanceFunctions: ComponentInfo[];
  allAnalysisMethods: ComponentInfo[];
}) {
  const store = useExperimentStore();
  const corporaMap = new Map(corpora.map((c) => [c.id, c]));

  const findDisplayName = (list: ComponentInfo[], name: string) => {
    const item = list.find((c) => c.name === name);
    return item ? item.display_name : name;
  };

  const sectionStyle: React.CSSProperties = {
    marginBottom: '1rem',
    padding: '0.75rem 1rem',
    background: '#16213e',
    borderRadius: '6px',
    border: '1px solid #2a2a4a',
  };

  const labelStyle: React.CSSProperties = {
    fontSize: '0.8rem',
    color: '#8888aa',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '0.35rem',
  };

  return (
    <div>
      <div style={sectionStyle}>
        <div style={labelStyle}>Experiment Name</div>
        <div style={{ fontWeight: 600, fontSize: '1.05rem' }}>{store.name}</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div style={sectionStyle}>
          <div style={labelStyle}>Known Corpora</div>
          {store.knownCorpusIds.length === 0 ? (
            <span style={{ color: '#8888aa' }}>None selected</span>
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
        <div style={sectionStyle}>
          <div style={labelStyle}>Unknown Corpora</div>
          {store.unknownCorpusIds.length === 0 ? (
            <span style={{ color: '#8888aa' }}>None selected</span>
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

      <div style={sectionStyle}>
        <div style={labelStyle}>Canonicizers</div>
        {store.canonicizers.length === 0 ? (
          <span style={{ color: '#8888aa' }}>None</span>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {store.canonicizers.map((c) => (
              <span
                key={c.name}
                style={{
                  padding: '0.25rem 0.6rem',
                  background: '#1a1a2e',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  border: '1px solid #2a2a4a',
                }}
              >
                {findDisplayName(allCanonicizers, c.name)}
                {Object.keys(c.params).length > 0 && (
                  <span style={{ color: '#8888aa', marginLeft: '0.4rem', fontSize: '0.75rem' }}>
                    ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>Event Drivers</div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {store.eventDrivers.map((c) => (
            <span
              key={c.name}
              style={{
                padding: '0.25rem 0.6rem',
                background: '#1a1a2e',
                borderRadius: '4px',
                fontSize: '0.85rem',
                border: '1px solid #2a2a4a',
              }}
            >
              {findDisplayName(allEventDrivers, c.name)}
              {Object.keys(c.params).length > 0 && (
                <span style={{ color: '#8888aa', marginLeft: '0.4rem', fontSize: '0.75rem' }}>
                  ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                </span>
              )}
            </span>
          ))}
        </div>
      </div>

      <div style={sectionStyle}>
        <div style={labelStyle}>Event Cullers</div>
        {store.eventCullers.length === 0 ? (
          <span style={{ color: '#8888aa' }}>None</span>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {store.eventCullers.map((c) => (
              <span
                key={c.name}
                style={{
                  padding: '0.25rem 0.6rem',
                  background: '#1a1a2e',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  border: '1px solid #2a2a4a',
                }}
              >
                {findDisplayName(allEventCullers, c.name)}
                {Object.keys(c.params).length > 0 && (
                  <span style={{ color: '#8888aa', marginLeft: '0.4rem', fontSize: '0.75rem' }}>
                    ({Object.entries(c.params).map(([k, v]) => `${k}=${v}`).join(', ')})
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div style={sectionStyle}>
          <div style={labelStyle}>Distance Function</div>
          <span style={{ fontSize: '0.9rem' }}>
            {store.distanceFunction
              ? findDisplayName(allDistanceFunctions, store.distanceFunction.name)
              : 'None'}
          </span>
          {store.distanceFunction && Object.keys(store.distanceFunction.params).length > 0 && (
            <span style={{ color: '#8888aa', marginLeft: '0.4rem', fontSize: '0.75rem' }}>
              ({Object.entries(store.distanceFunction.params).map(([k, v]) => `${k}=${v}`).join(', ')})
            </span>
          )}
        </div>
        <div style={sectionStyle}>
          <div style={labelStyle}>Analysis Method</div>
          <span style={{ fontSize: '0.9rem' }}>
            {findDisplayName(allAnalysisMethods, store.analysisMethod.name)}
          </span>
          {Object.keys(store.analysisMethod.params).length > 0 && (
            <span style={{ color: '#8888aa', marginLeft: '0.4rem', fontSize: '0.75rem' }}>
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
        return true; // optional
      case 4:
        return store.distanceFunction !== null;
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
    createExperiment.mutate(
      {
        name: store.name,
        config: store.getConfig(),
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
            <p style={{ color: '#8888aa', fontSize: '0.85rem', marginBottom: '1rem' }}>
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
            <p style={{ color: '#8888aa', fontSize: '0.85rem', marginBottom: '1rem' }}>
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
            <p style={{ color: '#8888aa', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Filter extracted events. Optional.
            </p>
            <ComponentSelector
              components={eventCullers}
              selected={store.eventCullers}
              onChange={store.setEventCullers}
              isLoading={eventCullersLoading}
              multiSelect
            />
          </div>
        );
      case 4:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Distance Function</h2>
            <p style={{ color: '#8888aa', fontSize: '0.85rem', marginBottom: '1rem' }}>
              How to measure distance between event distributions. Select one.
            </p>
            <ComponentSelector
              components={distanceFunctions}
              selected={store.distanceFunction ? [store.distanceFunction] : []}
              onChange={(specs) => store.setDistanceFunction(specs[0] ?? null)}
              isLoading={distanceFunctionsLoading}
              multiSelect={false}
            />
          </div>
        );
      case 5:
        return (
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>Analysis Method</h2>
            <p style={{ color: '#8888aa', fontSize: '0.85rem', marginBottom: '1rem' }}>
              The method used to determine authorship attribution. Select one.
            </p>
            <ComponentSelector
              components={analysisMethods}
              selected={[store.analysisMethod]}
              onChange={(specs) => {
                if (specs.length > 0) store.setAnalysisMethod(specs[0]);
              }}
              isLoading={analysisMethodsLoading}
              multiSelect={false}
            />
          </div>
        );
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
            />
            {submitError && (
              <div
                style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  background: 'rgba(248, 113, 113, 0.1)',
                  border: '1px solid #f87171',
                  borderRadius: '6px',
                  color: '#f87171',
                  fontSize: '0.9rem',
                }}
              >
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
      <div style={stepIndicatorRow}>
        {STEPS.map((label, i) => {
          const isActive = i === step;
          const isCompleted = i < step;
          return (
            <button
              key={i}
              onClick={() => {
                // Allow clicking on completed steps or current step
                if (i <= step) setStep(i);
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.75rem',
                borderRadius: '20px',
                fontSize: '0.8rem',
                fontWeight: isActive ? 600 : 400,
                border: isActive
                  ? '1px solid #7c8cf8'
                  : isCompleted
                    ? '1px solid #4ade80'
                    : '1px solid #2a2a4a',
                background: isActive ? 'rgba(124, 140, 248, 0.15)' : 'transparent',
                color: isActive ? '#7c8cf8' : isCompleted ? '#4ade80' : '#8888aa',
                cursor: i <= step ? 'pointer' : 'default',
                opacity: i > step ? 0.5 : 1,
              }}
            >
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  fontSize: '0.7rem',
                  fontWeight: 'bold',
                  background: isActive
                    ? '#7c8cf8'
                    : isCompleted
                      ? '#4ade80'
                      : '#2a2a4a',
                  color: isActive || isCompleted ? '#fff' : '#8888aa',
                }}
              >
                {isCompleted ? '\u2713' : i + 1}
              </span>
              {label}
            </button>
          );
        })}
      </div>

      {/* Step content */}
      <div style={cardStyle}>{renderStep()}</div>

      {/* Navigation buttons */}
      <div style={navRow}>
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
