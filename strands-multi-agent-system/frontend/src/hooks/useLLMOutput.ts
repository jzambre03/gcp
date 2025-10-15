import { useQuery } from '@tanstack/react-query';
import { servicesApi } from '@/lib/api';

export function useLLMOutput(serviceId: string) {
  return useQuery({
    queryKey: ['llm-output', serviceId],
    queryFn: () => servicesApi.getLLMOutput(serviceId),
    enabled: !!serviceId,
    retry: 1,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}


