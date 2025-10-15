import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, FileCode, Lightbulb } from 'lucide-react';
import type { DriftItem as DriftItemType, RiskLevel } from '@/types/drift';
import { getRiskColor } from '@/lib/utils';

interface DriftItemProps {
  item: DriftItemType;
  severity: RiskLevel;
}

export function DriftItem({ item, severity }: DriftItemProps) {
  const riskLabels = {
    high: 'HIGH RISK',
    medium: 'MEDIUM RISK',
    low: 'LOW RISK',
    allowed: 'ALLOWED',
  };

  return (
    <Card className="mb-4">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Badge className={getRiskColor(severity)}>
                {riskLabels[severity]}
              </Badge>
              {item.drift_category && (
                <Badge variant="outline">{item.drift_category}</Badge>
              )}
            </div>
            <CardTitle className="text-base flex items-start gap-2">
              <FileCode className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
              <span className="break-all">{item.file}</span>
            </CardTitle>
            <div className="text-sm text-muted-foreground">
              <span className="font-mono">{item.locator.value}</span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* AI Review Assistant */}
        {item.ai_review_assistant && (
          <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 space-y-3">
            <div className="flex items-center gap-2 text-blue-900 font-semibold">
              <Lightbulb className="h-4 w-4" />
              <span>AI Review Assistant</span>
            </div>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-semibold text-blue-900">Potential Risk:</span>
                <p className="text-blue-800 mt-1">{item.ai_review_assistant.potential_risk}</p>
              </div>
              <div>
                <span className="font-semibold text-blue-900">Suggested Action:</span>
                <p className="text-blue-800 mt-1">{item.ai_review_assistant.suggested_action}</p>
              </div>
            </div>
          </div>
        )}

        {/* Rationale for allowed variance */}
        {item.rationale && (
          <div className="rounded-lg bg-green-50 border border-green-200 p-4">
            <div className="flex items-center gap-2 text-green-900 font-semibold mb-2">
              <AlertCircle className="h-4 w-4" />
              <span>Rationale</span>
            </div>
            <p className="text-sm text-green-800">{item.rationale}</p>
          </div>
        )}

        {/* Changed values */}
        <div className="space-y-2">
          <div className="text-sm font-semibold">Configuration Change:</div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Previous</div>
              <div className="rounded border bg-red-50 border-red-200 p-2 text-sm font-mono break-all">
                {item.old !== null ? item.old : <span className="text-muted-foreground italic">null</span>}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Current</div>
              <div className="rounded border bg-green-50 border-green-200 p-2 text-sm font-mono break-all">
                {item.new !== null ? item.new : <span className="text-muted-foreground italic">null</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Remediation */}
        {item.remediation && (
          <div className="rounded-lg bg-gray-50 border border-gray-200 p-3">
            <div className="text-xs font-semibold text-gray-700 mb-2">Remediation Snippet:</div>
            <pre className="text-xs font-mono text-gray-800 overflow-x-auto">
              {item.remediation.snippet}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}


