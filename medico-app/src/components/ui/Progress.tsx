import { cn } from '../../lib/utils';

interface ProgressProps {
  value: number; // 0-100
  className?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow';
}

export function Progress({ value, className, color = 'blue' }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div className={cn('w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden', className)}>
      <div
        className={cn(
          'h-full rounded-full transition-all duration-300',
          color === 'blue' && 'bg-blue-500',
          color === 'green' && 'bg-green-500',
          color === 'red' && 'bg-red-500',
          color === 'yellow' && 'bg-yellow-500',
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
