import { useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentsApi } from '../api/experiments';
import type { ExperimentCreate } from '../types';
import { useExperimentStore } from '../store/experimentStore';

export function useCreateExperiment() {
  const queryClient = useQueryClient();
  const reset = useExperimentStore((s) => s.reset);

  return useMutation({
    mutationFn: (data: ExperimentCreate) => experimentsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      reset();
    },
  });
}
