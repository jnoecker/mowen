import { create } from 'zustand';
import type { ComponentSpec, ExperimentConfig } from '../types';

interface ExperimentStore {
  // Wizard state
  name: string;
  knownCorpusIds: number[];
  unknownCorpusIds: number[];
  canonicizers: ComponentSpec[];
  eventDrivers: ComponentSpec[];
  eventCullers: ComponentSpec[];
  distanceFunction: ComponentSpec | null;
  analysisMethod: ComponentSpec;

  // Actions
  setName: (name: string) => void;
  setKnownCorpusIds: (ids: number[]) => void;
  setUnknownCorpusIds: (ids: number[]) => void;
  setCanonicizers: (specs: ComponentSpec[]) => void;
  setEventDrivers: (specs: ComponentSpec[]) => void;
  setEventCullers: (specs: ComponentSpec[]) => void;
  setDistanceFunction: (spec: ComponentSpec | null) => void;
  setAnalysisMethod: (spec: ComponentSpec) => void;

  // Derived / bulk
  getConfig: () => ExperimentConfig;
  reset: () => void;
  loadFromConfig: (name: string, config: ExperimentConfig, knownCorpusIds: number[], unknownCorpusIds: number[]) => void;
}

const initialState = {
  name: '',
  knownCorpusIds: [] as number[],
  unknownCorpusIds: [] as number[],
  canonicizers: [] as ComponentSpec[],
  eventDrivers: [] as ComponentSpec[],
  eventCullers: [] as ComponentSpec[],
  distanceFunction: { name: 'cosine', params: {} } as ComponentSpec | null,
  analysisMethod: { name: 'nearest_neighbor', params: {} } as ComponentSpec,
};

export const useExperimentStore = create<ExperimentStore>((set, get) => ({
  ...initialState,

  setName: (name) => set({ name }),
  setKnownCorpusIds: (ids) => set({ knownCorpusIds: ids }),
  setUnknownCorpusIds: (ids) => set({ unknownCorpusIds: ids }),
  setCanonicizers: (specs) => set({ canonicizers: specs }),
  setEventDrivers: (specs) => set({ eventDrivers: specs }),
  setEventCullers: (specs) => set({ eventCullers: specs }),
  setDistanceFunction: (spec) => set({ distanceFunction: spec }),
  setAnalysisMethod: (spec) => set({ analysisMethod: spec }),

  getConfig: (): ExperimentConfig => {
    const state = get();
    return {
      canonicizers: state.canonicizers,
      event_drivers: state.eventDrivers,
      event_cullers: state.eventCullers,
      distance_function: state.distanceFunction,
      analysis_method: state.analysisMethod,
    };
  },

  reset: () => set({ ...initialState }),

  loadFromConfig: (name, config, knownCorpusIds, unknownCorpusIds) =>
    set({
      name,
      knownCorpusIds,
      unknownCorpusIds,
      canonicizers: config.canonicizers,
      eventDrivers: config.event_drivers,
      eventCullers: config.event_cullers,
      distanceFunction: config.distance_function,
      analysisMethod: config.analysis_method,
    }),
}));
