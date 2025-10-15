import { useServices, useAnalyzeService } from '@/hooks/useServices';
import { ServiceCard } from '@/components/dashboard/ServiceCard';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';

export function Overview() {
  const { data: services, isLoading, error } = useServices();
  const { mutate: analyze, isPending: isAnalyzing } = useAnalyzeService();

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-8">
        <div className="flex items-center gap-2 text-red-600">
          <AlertCircle className="h-5 w-5" />
          <p>Failed to load services: {(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-8">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Services Overview</h1>
          <p className="text-muted-foreground mt-2">
            Monitor and analyze configuration drift across all services
          </p>
        </div>

        {/* Services Grid */}
        {services && services.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => (
              <ServiceCard
                key={service.id}
                service={service}
                onAnalyze={() => analyze(service.id)}
                isAnalyzing={isAnalyzing}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            <p>No services configured</p>
          </div>
        )}
      </div>
    </div>
  );
}


