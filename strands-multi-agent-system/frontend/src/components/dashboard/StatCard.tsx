import { Card, CardContent } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: number | string;
  icon?: LucideIcon;
  variant?: 'default' | 'danger' | 'warning' | 'success';
  className?: string;
}

export function StatCard({ title, value, icon: Icon, variant = 'default', className }: StatCardProps) {
  const variantClasses = {
    default: 'border-gray-200',
    danger: 'border-red-200 bg-red-50/50',
    warning: 'border-orange-200 bg-orange-50/50',
    success: 'border-green-200 bg-green-50/50',
  };

  const textClasses = {
    default: 'text-gray-900',
    danger: 'text-red-700',
    warning: 'text-orange-700',
    success: 'text-green-700',
  };

  return (
    <Card className={cn('border-2', variantClasses[variant], className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={cn('text-3xl font-bold', textClasses[variant])}>
              {value}
            </p>
          </div>
          {Icon && (
            <Icon className={cn('h-8 w-8', textClasses[variant])} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}


