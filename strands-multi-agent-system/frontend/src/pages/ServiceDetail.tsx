import { useParams, Link } from 'react-router-dom';
import { useService, useAnalyzeService } from '@/hooks/useServices';
import { useLLMOutput } from '@/hooks/useLLMOutput';
import { StatCard } from '@/components/dashboard/StatCard';
import { DriftList } from '@/components/dashboard/DriftList';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  ArrowLeft, 
  FileText, 
  GitBranch, 
  AlertTriangle, 
  AlertCircle,
  Play,
  RefreshCw
} from 'lucide-react';
import { getEnvironmentColor } from '@/lib/utils';

export function ServiceDetail() {
  const { serviceId } = useParams<{ serviceId: string }>();
  const { data: service } = useService(serviceId!);
  const { data: llmOutput, isLoading, error, refetch } = useLLMOutput(serviceId!);
  const { mutate: analyze, isPending: isAnalyzing } = useAnalyzeService();

  if (!serviceId) {
    return <div>Service ID not found</div>;
  }

  if (isLoading) {
    return (
      <div className="container py-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-8">
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground" />
          <div className="text-center space-y-2">
            <h3 className="font-semibold text-lg">No Analysis Results Yet</h3>
            <p className="text-muted-foreground">
              Click "Run Analysis" to start analyzing configuration drift
            </p>
          </div>
          <Button onClick={() => analyze(serviceId)} disabled={isAnalyzing}>
            <Play className="h-4 w-4 mr-2" />
            {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
          </Button>
        </div>
      </div>
    );
  }

  if (!llmOutput) {
    return null;
  }

  return (
    <div className="container py-8 space-y-6">
      {/* Breadcrumb & Header */}
      <div className="space-y-4">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Services
        </Link>
        
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{service?.name || serviceId}</h1>
              {service && (
                <Badge className={getEnvironmentColor(service.environment)}>
                  {service.environment.toUpperCase()}
                </Badge>
              )}
            </div>
            <div className="flex items-center text-sm text-muted-foreground">
              <GitBranch className="h-4 w-4 mr-2" />
              <span>{service?.golden_branch} → {service?.drift_branch}</span>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={() => analyze(serviceId)} disabled={isAnalyzing}>
              <Play className="h-4 w-4 mr-2" />
              {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Config Files"
          value={llmOutput.summary.total_config_files}
          icon={FileText}
        />
        <StatCard
          title="Files with Drift"
          value={llmOutput.summary.files_with_drift}
          icon={GitBranch}
        />
        <StatCard
          title="Total Drifts"
          value={llmOutput.summary.total_drifts}
          icon={AlertTriangle}
        />
        <StatCard
          title="High Risk"
          value={llmOutput.summary.high_risk}
          icon={AlertCircle}
          variant={llmOutput.summary.high_risk > 0 ? 'danger' : 'default'}
        />
      </div>

      {/* Drift Tabs */}
      <Tabs defaultValue="high" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="high">
            High Risk ({llmOutput.summary.high_risk})
          </TabsTrigger>
          <TabsTrigger value="medium">
            Medium Risk ({llmOutput.summary.medium_risk})
          </TabsTrigger>
          <TabsTrigger value="low">
            Low Risk ({llmOutput.summary.low_risk})
          </TabsTrigger>
          <TabsTrigger value="allowed">
            Allowed ({llmOutput.summary.allowed_variance})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="high" className="mt-6">
          <DriftList items={llmOutput.high} severity="high" />
        </TabsContent>

        <TabsContent value="medium" className="mt-6">
          <DriftList items={llmOutput.medium} severity="medium" />
        </TabsContent>

        <TabsContent value="low" className="mt-6">
          <DriftList items={llmOutput.low} severity="low" />
        </TabsContent>

        <TabsContent value="allowed" className="mt-6">
          <DriftList items={llmOutput.allowed_variance} severity="allowed" />
        </TabsContent>
      </Tabs>
    </div>
  );
}


