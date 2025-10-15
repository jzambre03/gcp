import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { servicesApi } from '@/lib/api';
import { toast } from 'sonner';

export function useServices() {
  return useQuery({
    queryKey: ['services'],
    queryFn: servicesApi.getAll,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useService(serviceId: string) {
  return useQuery({
    queryKey: ['service', serviceId],
    queryFn: () => servicesApi.getById(serviceId),
    enabled: !!serviceId,
  });
}

export function useAnalyzeService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serviceId: string) => servicesApi.analyze(serviceId),
    onSuccess: (data) => {
      toast.success('Analysis started', {
        description: `Running drift analysis for ${data.service_id}`,
      });
      
      // Invalidate LLM output query to refetch after analysis
      setTimeout(() => {
        queryClient.invalidateQueries({ 
          queryKey: ['llm-output', data.service_id] 
        });
      }, 5000); // Wait 5 seconds for analysis to complete
    },
    onError: (error: any) => {
      toast.error('Analysis failed', {
        description: error.response?.data?.detail || error.message,
      });
    },
  });
}


