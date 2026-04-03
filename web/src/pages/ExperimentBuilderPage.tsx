import { useId, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { pipelineApi } from '../api/pipeline';
import { corporaApi } from '../api/corpora';
import { useExperimentStore } from '../store/experimentStore';
import { useCreateExperiment } from '../hooks/useExperiment';
import type { ComponentInfo, ComponentSpec, CorpusResponse, ParamInfo, ParamValue } from '../types';
import { PRESETS } from '../presets';
import type { Preset } from '../presets';
import s from './ExperimentBuilderPage.module.css';

const PHASES = [
  { label: 'Inquiry', caption: 'Name the study and choose corpora' },
  { label: 'Preparation', caption: 'Decide how much text to normalize' },
  { label: 'Evidence', caption: 'Choose signals and comparison rules' },
  { label: 'Judgement', caption: 'Select the method and review the folio' },
] as const;

function fmtParams(params: ComponentSpec['params']) {
  const entries = Object.entries(params);
  return entries.length ? entries.map(([k, v]) => `${k}=${String(v)}`).join(', ') : null;
}

function PhaseIntro({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className={s.phaseIntro}>
      <p className={s.phaseEyebrow}>{eyebrow}</p>
      <h2 className={s.phaseTitle}>{title}</h2>
      <p className={s.phaseBody}>{description}</p>
    </div>
  );
}

function ParameterEditor({
  params,
  values,
  onChange,
  idPrefix,
}: {
  params: ParamInfo[];
  values: ComponentSpec['params'];
  onChange: (name: string, value: ParamValue) => void;
  idPrefix: string;
}) {
  return (
    <div className={s.paramFields}>
      {params.map((param) => {
        const value = values[param.name] ?? param.default ?? '';
        const fieldId = `${idPrefix}-${param.name}`.replace(/[^a-zA-Z0-9_-]/g, '-').toLowerCase();
        const isBoolean = param.type === 'bool' || param.type === 'boolean';
        const isNumeric = param.type === 'int' || param.type === 'float';

        if (param.choices && param.choices.length > 0) {
          return (
            <div key={param.name} className={s.paramField}>
              <label className={s.paramLabel} htmlFor={fieldId}>
                {param.name}
                {param.description && <span className={s.paramHint}>{param.description}</span>}
              </label>
              <select id={fieldId} value={String(value)} className={s.paramInput} onChange={(e) => onChange(param.name, e.target.value)}>
                {param.choices.map((choice) => (
                  <option key={String(choice)} value={String(choice)}>
                    {String(choice)}
                  </option>
                ))}
              </select>
            </div>
          );
        }

        if (isBoolean) {
          return (
            <label key={param.name} className={s.booleanField} htmlFor={fieldId}>
              <input id={fieldId} type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(param.name, e.target.checked)} />
              <span>
                <span className={s.booleanLabel}>{param.name}</span>
                {param.description && <span className={s.booleanHint}>{param.description}</span>}
              </span>
            </label>
          );
        }

        return (
          <div key={param.name} className={s.paramField}>
            <label className={s.paramLabel} htmlFor={fieldId}>
              {param.name}
              {param.description && <span className={s.paramHint}>{param.description}</span>}
            </label>
            <input
              id={fieldId}
              className={s.paramInput}
              type={isNumeric ? 'number' : 'text'}
              value={typeof value === 'string' || typeof value === 'number' ? value : ''}
              min={param.min_value ?? undefined}
              max={param.max_value ?? undefined}
              step={param.type === 'float' ? 'any' : undefined}
              onChange={(e) => {
                const raw = e.target.value;
                onChange(
                  param.name,
                  isNumeric ? (raw === '' ? '' : param.type === 'int' ? parseInt(raw, 10) : parseFloat(raw)) : raw,
                );
              }}
            />
          </div>
        );
      })}
    </div>
  );
}

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
  const groupId = useId();
  if (isLoading) return <p className={s.helperText}>Loading options...</p>;
  if (components.length === 0) return <p className={s.helperText}>No options are available.</p>;

  const selectedMap = new Map(selected.map((item) => [item.name, item]));

  const defaultsFor = (component: ComponentInfo) => {
    const defaults: ComponentSpec['params'] = {};
    component.params?.forEach((param) => {
      if (param.default !== null && param.default !== undefined) defaults[param.name] = param.default;
    });
    return defaults;
  };

  const toggle = (component: ComponentInfo) => {
    if (multiSelect) {
      if (selectedMap.has(component.name)) {
        onChange(selected.filter((item) => item.name !== component.name));
      } else {
        onChange([...selected, { name: component.name, params: defaultsFor(component) }]);
      }
      return;
    }
    if (!selectedMap.has(component.name)) onChange([{ name: component.name, params: defaultsFor(component) }]);
  };

  return (
    <fieldset className={s.fieldset}>
      <legend className={s.srOnlyLegend}>{multiSelect ? 'Select one or more options' : 'Select one option'}</legend>
      <div className={s.componentGrid}>
        {components.map((component) => {
          const isSelected = selectedMap.has(component.name);
          const spec = selectedMap.get(component.name);
          const inputId = `${groupId}-${component.name}`.replace(/[^a-zA-Z0-9_-]/g, '-').toLowerCase();

          return (
            <div key={component.name} className={s.componentChoice}>
              <input
                id={inputId}
                className={s.choiceInput}
                type={multiSelect ? 'checkbox' : 'radio'}
                name={multiSelect ? inputId : groupId}
                checked={isSelected}
                onChange={() => toggle(component)}
              />
              <label htmlFor={inputId} className={`${s.componentCard} ${isSelected ? s.componentCardSelected : ''}`}>
                <div className={s.componentHeader}>
                  <div className={s.componentCopy}>
                    <div className={s.componentNameRow}>
                      <span className={s.componentName}>{component.display_name}</span>
                      {component.numeric && <span className={s.componentTag}>embedding</span>}
                    </div>
                    <div className={s.componentSlug}>{component.name}</div>
                  </div>
                  <div className={`${multiSelect ? s.checkbox : s.radio} ${isSelected ? s.choiceIndicatorSelected : ''}`} aria-hidden="true">
                    {isSelected && <span className={s.checkmark}>{multiSelect ? '\u2713' : '\u25CF'}</span>}
                  </div>
                </div>
                {component.description && <p className={s.componentDesc}>{component.description}</p>}
              </label>
              {isSelected && component.params && component.params.length > 0 && spec && (
                <div className={s.paramShell}>
                  <ParameterEditor
                    params={component.params}
                    values={spec.params}
                    onChange={(paramName, value) =>
                      onChange(selected.map((item) => (item.name === component.name ? { ...item, params: { ...item.params, [paramName]: value } } : item)))
                    }
                    idPrefix={inputId}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </fieldset>
  );
}

function StepNameCorpora({
  corpora,
  isLoading,
  onApplyPreset,
  activePresetId,
}: {
  corpora: CorpusResponse[];
  isLoading: boolean;
  onApplyPreset: (preset: Preset) => void;
  activePresetId: string | null;
}) {
  const experimentNameId = useId();
  const name = useExperimentStore((state) => state.name);
  const setName = useExperimentStore((state) => state.setName);
  const knownCorpusIds = useExperimentStore((state) => state.knownCorpusIds);
  const setKnownCorpusIds = useExperimentStore((state) => state.setKnownCorpusIds);
  const unknownCorpusIds = useExperimentStore((state) => state.unknownCorpusIds);
  const setUnknownCorpusIds = useExperimentStore((state) => state.setUnknownCorpusIds);
  const toggleCorpus = (ids: number[], setIds: (ids: number[]) => void, id: number) => setIds(ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id]);

  return (
    <div className={s.stepStack}>
      <PhaseIntro
        eyebrow="Inquiry"
        title="Frame the question before tuning the method"
        description="Start from a published baseline when you can. Then name the study and separate reference texts from questioned ones."
      />

      <section className={s.sectionBlock}>
        <p className={s.sectionLabel}>Literature-backed starting points</p>
        <h3 className={s.sectionTitle}>Begin from a known method</h3>
        <p className={s.sectionLead}>Pick a preset for a defensible baseline, then revise only the pieces your question demands.</p>
        <fieldset className={s.presetFieldset}>
          <legend className={s.srOnlyLegend}>Select an experiment preset</legend>
          <div className={s.presetGrid}>
            {PRESETS.map((preset) => (
              <div key={preset.id} className={s.componentChoice}>
                <input id={`preset-${preset.id}`} className={s.choiceInput} type="radio" name="experiment-preset" checked={activePresetId === preset.id} onChange={() => onApplyPreset(preset)} />
                <label htmlFor={`preset-${preset.id}`} className={`${s.presetCard} ${activePresetId === preset.id ? s.presetCardActive : ''}`}>
                  <div className={s.presetName}>{preset.name}</div>
                  <div className={s.presetDesc}>{preset.description}</div>
                  <div className={s.presetCitation}>{preset.citation}</div>
                </label>
              </div>
            ))}
          </div>
        </fieldset>
      </section>

      <div className={s.sectionDivider}>then situate the study</div>

      <section className={s.sectionBlock}>
        <p className={s.sectionLabel}>Study framing</p>
        <h3 className={s.sectionTitle}>Name the inquiry</h3>
        <p className={s.sectionLead}>Use a title that will still make sense when you compare several methodological variations later.</p>
        <label className={s.paramLabel} htmlFor={experimentNameId}>Experiment title</label>
        <input id={experimentNameId} value={name} onChange={(e) => setName(e.target.value)} placeholder="Burrows Delta on political letters" className={`${s.paramInput} ${s.nameInput}`} />
      </section>

      <section className={s.sectionBlock}>
        <p className={s.sectionLabel}>Corpus shelves</p>
        <h3 className={s.sectionTitle}>Set apart reference voices and questioned texts</h3>
        <p className={s.sectionLead}>The known corpus teaches the model what candidate authors sound like. The unknown corpus holds the texts you want judged.</p>
        {isLoading && <p className={s.helperText}>Loading corpora...</p>}
        {!isLoading && corpora.length === 0 && <p className={s.helperText}>No corpora are available yet. Create corpora before composing an experiment.</p>}
        {!isLoading && corpora.length > 0 && (
          <div className={s.corporaGrid}>
            <fieldset className={s.fieldset}>
              <legend className={s.corpusLegend}>Reference shelves</legend>
              <p className={s.corpusHelp}>Known-author material used as training evidence.</p>
              <div className={s.corporaList}>
                {corpora.map((corpus) => (
                  <label key={corpus.id} className={s.corpusLabel}>
                    <input type="checkbox" checked={knownCorpusIds.includes(corpus.id)} onChange={() => toggleCorpus(knownCorpusIds, setKnownCorpusIds, corpus.id)} />
                    <span className={s.corpusName}>{corpus.name}</span>
                    <span className={s.corpusCount}>{corpus.document_count} doc{corpus.document_count !== 1 ? 's' : ''}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <fieldset className={s.fieldset}>
              <legend className={s.corpusLegend}>Questioned texts</legend>
              <p className={s.corpusHelp}>Documents whose authorship you want the experiment to judge.</p>
              <div className={s.corporaList}>
                {corpora.map((corpus) => (
                  <label key={corpus.id} className={s.corpusLabel}>
                    <input type="checkbox" checked={unknownCorpusIds.includes(corpus.id)} onChange={() => toggleCorpus(unknownCorpusIds, setUnknownCorpusIds, corpus.id)} />
                    <span className={s.corpusName}>{corpus.name}</span>
                    <span className={s.corpusCount}>{corpus.document_count} doc{corpus.document_count !== 1 ? 's' : ''}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>
        )}
      </section>
    </div>
  );
}

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
  const corporaMap = new Map(corpora.map((corpus) => [corpus.id, corpus]));
  const findName = (list: ComponentInfo[], name: string) => list.find((item) => item.name === name)?.display_name ?? name;
  const known = store.knownCorpusIds.map((id) => corporaMap.get(id)?.name ?? `Corpus #${id}`);
  const unknown = store.unknownCorpusIds.map((id) => corporaMap.get(id)?.name ?? `Corpus #${id}`);

  return (
    <div className={s.reviewStack}>
      <div className={s.reviewPanel}>
        <p className={s.reviewLabel}>Inquiry title</p>
        <div className={s.reviewValue}>{store.name}</div>
      </div>
      <div className={s.reviewGrid}>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Reference shelves</p>
          {known.length === 0 ? <p className={s.helperText}>None selected</p> : <ul className={s.reviewList}>{known.map((name) => <li key={name}>{name}</li>)}</ul>}
        </div>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Questioned texts</p>
          {unknown.length === 0 ? <p className={s.helperText}>None selected</p> : <ul className={s.reviewList}>{unknown.map((name) => <li key={name}>{name}</li>)}</ul>}
        </div>
      </div>
      <div className={s.reviewGrid}>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Text preparation</p>
          {store.canonicizers.length === 0 ? <p className={s.helperText}>Original text surface preserved.</p> : <div className={s.reviewChips}>{store.canonicizers.map((item) => <span key={item.name} className={s.reviewChip}>{findName(allCanonicizers, item.name)}{fmtParams(item.params) && <span className={s.reviewChipParams}>{fmtParams(item.params)}</span>}</span>)}</div>}
        </div>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Stylistic signals</p>
          <div className={s.reviewChips}>{store.eventDrivers.map((item) => <span key={item.name} className={s.reviewChip}>{findName(allEventDrivers, item.name)}{fmtParams(item.params) && <span className={s.reviewChipParams}>{fmtParams(item.params)}</span>}</span>)}</div>
        </div>
      </div>
      <div className={s.reviewGrid}>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Feature filtering</p>
          {numericMode ? <p className={s.helperText}>Skipped because embedding-based signals are selected.</p> : store.eventCullers.length === 0 ? <p className={s.helperText}>No additional culling applied.</p> : <div className={s.reviewChips}>{store.eventCullers.map((item) => <span key={item.name} className={s.reviewChip}>{findName(allEventCullers, item.name)}{fmtParams(item.params) && <span className={s.reviewChipParams}>{fmtParams(item.params)}</span>}</span>)}</div>}
        </div>
        <div className={s.reviewPanel}>
          <p className={s.reviewLabel}>Comparison rule</p>
          {numericMode ? <p className={s.helperText}>Handled internally by the selected numeric method.</p> : <div className={s.reviewValue}>{store.distanceFunction ? findName(allDistanceFunctions, store.distanceFunction.name) : 'None selected'}{store.distanceFunction && fmtParams(store.distanceFunction.params) && <span className={s.reviewInlineMeta}>{fmtParams(store.distanceFunction.params)}</span>}</div>}
        </div>
      </div>
      <div className={s.reviewPanel}>
        <p className={s.reviewLabel}>Final judgement method</p>
        <div className={s.reviewValue}>{findName(allAnalysisMethods, store.analysisMethod.name)}{fmtParams(store.analysisMethod.params) && <span className={s.reviewInlineMeta}>{fmtParams(store.analysisMethod.params)}</span>}</div>
      </div>
    </div>
  );
}

export default function ExperimentBuilderPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [activePresetId, setActivePresetId] = useState<string | null>(null);
  const store = useExperimentStore();
  const createExperiment = useCreateExperiment();
  const activePreset = PRESETS.find((preset) => preset.id === activePresetId) ?? null;

  const { data: corpora = [], isLoading: corporaLoading } = useQuery({ queryKey: ['corpora'], queryFn: corporaApi.list });
  const { data: canonicizers = [], isLoading: canonicizersLoading } = useQuery({ queryKey: ['pipeline', 'canonicizers'], queryFn: pipelineApi.getCanonicizers });
  const { data: eventDrivers = [], isLoading: eventDriversLoading } = useQuery({ queryKey: ['pipeline', 'event-drivers'], queryFn: pipelineApi.getEventDrivers });
  const { data: eventCullers = [], isLoading: eventCullersLoading } = useQuery({ queryKey: ['pipeline', 'event-cullers'], queryFn: pipelineApi.getEventCullers });
  const { data: distanceFunctions = [], isLoading: distanceFunctionsLoading } = useQuery({ queryKey: ['pipeline', 'distance-functions'], queryFn: pipelineApi.getDistanceFunctions });
  const { data: analysisMethods = [], isLoading: analysisMethodsLoading } = useQuery({ queryKey: ['pipeline', 'analysis-methods'], queryFn: pipelineApi.getAnalysisMethods });

  const numericMode = store.eventDrivers.some((driver) => eventDrivers.find((item) => item.name === driver.name)?.numeric === true);
  const canProceed = () => step === 0 ? store.name.trim().length > 0 && store.knownCorpusIds.length > 0 && store.unknownCorpusIds.length > 0 : step === 1 ? true : step === 2 ? store.eventDrivers.length > 0 && (numericMode || store.distanceFunction !== null) : store.analysisMethod.name.length > 0;

  const applyPreset = (preset: Preset) => {
    setActivePresetId(preset.id);
    store.setCanonicizers(preset.config.canonicizers);
    store.setEventDrivers(preset.config.event_drivers);
    store.setEventCullers(preset.config.event_cullers);
    store.setDistanceFunction(preset.config.distance_function);
    store.setAnalysisMethod(preset.config.analysis_method);
    if (!store.name.trim()) store.setName(preset.name);
  };

  const handleSubmit = () => {
    setSubmitError(null);
    const config = store.getConfig();
    if (numericMode) {
      config.event_cullers = [];
      config.distance_function = null;
    }
    createExperiment.mutate(
      { name: store.name, config, known_corpus_ids: store.knownCorpusIds, unknown_corpus_ids: store.unknownCorpusIds },
      {
        onSuccess: (experiment) => {
          setSubmitted(true);
          setTimeout(() => navigate(`/experiments/${experiment.id}/results`), 800);
        },
        onError: (error: Error) => setSubmitError(error.message || 'Failed to create experiment.'),
      },
    );
  };

  const renderStep = () => {
    if (step === 0) return <StepNameCorpora corpora={corpora} isLoading={corporaLoading} onApplyPreset={applyPreset} activePresetId={activePresetId} />;
    if (step === 1) {
      return (
        <div className={s.stepStack}>
          <PhaseIntro eyebrow="Preparation" title="Quiet the surface without erasing what matters" description="Normalization can help, but it can also remove evidence. Apply only the steps that support the question." />
          <section className={s.sectionBlock}>
            <p className={s.sectionLabel}>Text preparation</p>
            <h3 className={s.sectionTitle}>Choose optional canonicizers</h3>
            <p className={s.sectionLead}>Leave this empty if you want to preserve the original textual surface.</p>
            <ComponentSelector components={canonicizers} selected={store.canonicizers} onChange={(value) => { setActivePresetId(null); store.setCanonicizers(value); }} isLoading={canonicizersLoading} multiSelect />
          </section>
        </div>
      );
    }
    if (step === 2) {
      return (
        <div className={s.stepStack}>
          <PhaseIntro eyebrow="Evidence" title="Choose what traces of style the experiment should attend to" description="Select the stylistic signals first, then decide whether the method also needs filtering and an explicit distance rule." />
          <section className={s.sectionBlock}>
            <p className={s.sectionLabel}>Stylistic signals</p>
            <h3 className={s.sectionTitle}>Select the evidence source</h3>
            <p className={s.sectionLead}>Word frequencies, n-grams, function words, and embeddings each foreground different aspects of style.</p>
            <ComponentSelector components={eventDrivers} selected={store.eventDrivers} onChange={(value) => { setActivePresetId(null); store.setEventDrivers(value); }} isLoading={eventDriversLoading} multiSelect />
          </section>
          {numericMode ? (
            <div className={s.noteBlock}>
              <h3 className={s.noteTitle}>Embedding mode is active</h3>
              <p className={s.noteText}>Cullers and explicit distance functions are skipped here because the numeric method handles similarity internally.</p>
            </div>
          ) : (
            <>
              <section className={s.sectionBlock}>
                <p className={s.sectionLabel}>Feature filtering</p>
                <h3 className={s.sectionTitle}>Cull only if it helps the comparison</h3>
                <p className={s.sectionLead}>Use this to reduce noise or focus the analysis on the most informative features.</p>
                <ComponentSelector components={eventCullers} selected={store.eventCullers} onChange={(value) => { setActivePresetId(null); store.setEventCullers(value); }} isLoading={eventCullersLoading} multiSelect />
              </section>
              <section className={s.sectionBlock}>
                <p className={s.sectionLabel}>Comparison rule</p>
                <h3 className={s.sectionTitle}>Choose how stylistic distance is measured</h3>
                <p className={s.sectionLead}>Select one distance function for vector-based methods.</p>
                <ComponentSelector components={distanceFunctions} selected={store.distanceFunction ? [store.distanceFunction] : []} onChange={(specs) => { setActivePresetId(null); store.setDistanceFunction(specs[0] ?? null); }} isLoading={distanceFunctionsLoading} multiSelect={false} />
              </section>
            </>
          )}
        </div>
      );
    }

    const filteredMethods = numericMode ? analysisMethods.filter((item) => item.numeric === true) : analysisMethods;
    return (
      <div className={s.stepStack}>
        <PhaseIntro eyebrow="Judgement" title="Choose the deciding method, then review the full folio" description="The final method turns your selected evidence into an attribution judgement. Review the assembled configuration as one coherent study." />
        <section className={s.sectionBlock}>
          <p className={s.sectionLabel}>Decision layer</p>
          <h3 className={s.sectionTitle}>Select the attribution method</h3>
          <p className={s.sectionLead}>{numericMode ? 'Only methods compatible with embeddings are shown here.' : 'Choose the method that turns distances or features into an authorship judgement.'}</p>
          <ComponentSelector components={filteredMethods} selected={[store.analysisMethod]} onChange={(specs) => { if (specs.length > 0) { setActivePresetId(null); store.setAnalysisMethod(specs[0]); } }} isLoading={analysisMethodsLoading} multiSelect={false} />
        </section>
        <section className={s.sectionBlock}>
          <p className={s.sectionLabel}>Review</p>
          <h3 className={s.sectionTitle}>Read the experiment as a whole</h3>
          <p className={s.sectionLead}>A good experiment should read clearly from question to judgement.</p>
          <StepReview corpora={corpora} allCanonicizers={canonicizers} allEventDrivers={eventDrivers} allEventCullers={eventCullers} allDistanceFunctions={distanceFunctions} allAnalysisMethods={analysisMethods} numericMode={numericMode} />
        </section>
        <div aria-live="polite">{submitError && <div className={s.errorBox} role="alert">{submitError}</div>}</div>
      </div>
    );
  };

  const currentPhase = PHASES[step];
  const isFinalStep = step === PHASES.length - 1;

  return (
    <div className={s.pageShell}>
      <section className={`card ${s.pageIntro}`}>
        <div className={s.pageIntroCopy}>
          <p className={s.pageEyebrow}>Experiment folio</p>
          <h1 className={s.pageTitle}>Compose a stylometric inquiry</h1>
          <p className={s.pageLead}>The pipeline is still fully configurable, but the flow is organized around the scholar's task: frame a question, choose evidence, then defend the judgement.</p>
        </div>
        <div className={s.summaryStrip}>
          <div className={s.summaryItem}><span className={s.summaryLabel}>Starting point</span><span className={s.summaryValue}>{activePreset?.name ?? 'Custom folio'}</span></div>
          <div className={s.summaryItem}><span className={s.summaryLabel}>Corpora</span><span className={s.summaryValue}>{store.knownCorpusIds.length} reference / {store.unknownCorpusIds.length} questioned</span></div>
          <div className={s.summaryItem}><span className={s.summaryLabel}>Signals</span><span className={s.summaryValue}>{store.eventDrivers.length > 0 ? `${store.eventDrivers.length} selected` : 'Not chosen yet'}</span></div>
          <div className={s.summaryItem}><span className={s.summaryLabel}>Current phase</span><span className={s.summaryValue}>{currentPhase.label}</span></div>
        </div>
      </section>

      <div className={s.phaseRail}>
        {PHASES.map((phase, index) => {
          const isActive = index === step;
          const isCompleted = index < step;
          const isClickable = index <= step;
          return (
            <button key={phase.label} className={`${s.phaseButton} ${isActive ? s.phaseButtonCurrent : ''} ${isCompleted ? s.phaseButtonDone : ''}`} disabled={!isClickable} onClick={() => isClickable && setStep(index)}>
              <span className={s.phaseNumber}>{isCompleted ? '\u2713' : index + 1}</span>
              <span className={s.phaseMeta}>
                <span className={s.phaseName}>{phase.label}</span>
                <span className={s.phaseCaption}>{phase.caption}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className={`card ${s.workspaceCard}`}>{renderStep()}</div>

      <div className={s.navRow}>
        <button onClick={() => setStep((current) => current - 1)} disabled={step === 0}>Back</button>
        <div className={s.navMeta}>Phase {step + 1} of {PHASES.length}: {currentPhase.label}</div>
        {isFinalStep ? (
          <button className="primary" onClick={handleSubmit} disabled={createExperiment.isPending || submitted || !canProceed()}>
            {submitted ? '\u2713 Created - opening results...' : createExperiment.isPending ? 'Submitting...' : 'Run experiment'}
          </button>
        ) : (
          <button className="primary" onClick={() => setStep((current) => current + 1)} disabled={!canProceed()}>Next phase</button>
        )}
      </div>
    </div>
  );
}
