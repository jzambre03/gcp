import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, GitBranch, Play, Server } from 'lucide-react';
import type { Service } from '@/types/service';
import { getEnvironmentColor } from '@/lib/utils';

interface ServiceCardProps {
  service: Service;
  onAnalyze: () => void;
  isAnalyzing?: boolean;
}

export function ServiceCard({ service, onAnalyze, isAnalyzing }: ServiceCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-xl">{service.name}</CardTitle>
            <CardDescription className="flex items-center gap-2 mt-2">
              <Server className="h-3 w-3" />
              <span className="text-xs">{service.id}</span>
            </CardDescription>
          </div>
          <Badge className={getEnvironmentColor(service.environment)}>
            {service.environment.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex items-center text-sm text-muted-foreground">
          <GitBranch className="h-4 w-4 mr-2 flex-shrink-0" />
          <span className="truncate">
            {service.golden_branch} → {service.drift_branch}
          </span>
        </div>

        <div className="flex items-center gap-4 text-sm">
          {service.drift_count !== undefined && (
            <div className="flex items-center gap-1">
              <span className="font-semibold">{service.drift_count}</span>
              <span className="text-muted-foreground">drifts</span>
            </div>
          )}
          {service.high_risk !== undefined && service.high_risk > 0 && (
            <Badge variant="destructive" className="text-xs">
              {service.high_risk} high risk
            </Badge>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className="flex-1"
          size="sm"
        >
          <Play className="h-4 w-4 mr-2" />
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </Button>
        <Button variant="outline" size="sm" asChild>
          <Link to={`/service/${service.id}`}>
            View Details
            <ArrowRight className="h-4 w-4 ml-2" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}


