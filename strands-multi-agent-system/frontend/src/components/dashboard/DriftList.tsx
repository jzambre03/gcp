import { DriftItem } from './DriftItem';
import type { DriftItem as DriftItemType, RiskLevel } from '@/types/drift';

interface DriftListProps {
  items: DriftItemType[];
  severity: RiskLevel;
}

export function DriftList({ items, severity }: DriftListProps) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No {severity} risk items found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <DriftItem key={item.id} item={item} severity={severity} />
      ))}
    </div>
  );
}


