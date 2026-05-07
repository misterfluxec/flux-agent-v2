import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 text-center ${className}`}>
      <div className="p-4 bg-surface-2 rounded-full mb-4 animate-fade-in">
        <Icon className="w-8 h-8 text-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2 animate-fade-in" style={{ animationDelay: '100ms' }}>
        {title}
      </h3>
      <p className="text-sm text-text-secondary max-w-sm mb-6 animate-fade-in" style={{ animationDelay: '200ms' }}>
        {description}
      </p>
      {action && (
        <Button 
          onClick={action.onClick}
          className="animate-slide-up"
          style={{ animationDelay: '300ms' }}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
