import { Loader2 } from 'lucide-react';

export const ThinkingIndicator = () => {
  return (
    <div className="flex items-center gap-2 text-muted-foreground">
      <Loader2 size={16} className="animate-spin" />
      <span className="text-sm">Thinking...</span>
      <div className="flex gap-1">
        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
    </div>
  );
};
