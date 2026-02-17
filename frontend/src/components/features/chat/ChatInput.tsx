import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Plus, Square, ArrowUp } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/common/ui/button';
import { Textarea } from '@/components/common/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/common/ui/select";
import { cn } from '@/lib/utils';
import { logger } from '@/lib/logger';
import { useModels, type Model } from '@/hooks/useModels';
import { api } from '@/lib/api';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isProcessing?: boolean;
  placeholder?: string;
  className?: string;
}

export const ChatInput = ({
  onSend,
  onStop,
  disabled = false,
  isProcessing = false,
  placeholder = "How can I help you today?",
  className
}: ChatInputProps) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { data: models = [] } = useModels();
  const queryClient = useQueryClient();

  // Mutation for updating active model globally
  const updateModelMutation = useMutation({
    mutationFn: async (modelId: string) => {
      const model = (models as Model[]).find(m => m.id === modelId);
      if (!model) throw new Error("Model not found");

      const updatedConfig = { ...model, is_active: true };
      return api.put(`/admin/models/${modelId}`, updatedConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
    }
  });

  const activeModel = (models as Model[]).find(m => m.is_active) || models[0];
  const activeModelId = activeModel?.id || '';

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const maxHeight = 400;
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || disabled || isProcessing) return;
    logger.info("chat_message_sent", { length: input.length });
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleStop = () => {
    if (onStop) {
      logger.info("chat_generation_stopped");
      onStop();
    }
  };

  return (
    <div className={cn("w-full transition-all", className)}>
      <div className="max-w-4xl mx-auto pb-6">
        <div className={cn(
          "relative flex flex-col transition-all border border-border/40 rounded-[28px] overflow-hidden",
          "bg-muted/50 backdrop-blur-xl focus-within:border-primary/20",
          disabled && "opacity-50 grayscale pointer-events-none"
        )}>
          {/* Input Area */}
          <div className="px-5 pt-4">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled}
              className={cn(
                "min-h-15 max-h-100 w-full resize-none bg-transparent p-0 border-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 transition-all",
                "text-base leading-relaxed placeholder:text-muted-foreground/50"
              )}
            />
          </div>

          {/* Action Row */}
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full text-muted-foreground hover:bg-background/50 transition-colors"
                disabled={disabled || isProcessing}
                title="Attach file (Coming soon)"
              >
                <Plus size={20} />
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center">
                {updateModelMutation.isPending && (
                  <span className="text-[10px] text-muted-foreground animate-pulse mr-2">Updating...</span>
                )}
                <Select
                  value={activeModelId}
                  onValueChange={(id) => updateModelMutation.mutate(id)}
                  disabled={updateModelMutation.isPending || isProcessing}
                >
                  <SelectTrigger className="h-8 w-auto px-3 border-none bg-transparent hover:bg-background/50 rounded-xl gap-1.5 font-medium text-xs text-muted-foreground shadow-none focus:ring-0 transition-colors cursor-pointer">
                    <SelectValue placeholder="Model" />
                  </SelectTrigger>
                  <SelectContent className="rounded-2xl border-border bg-background/95 backdrop-blur-xl shadow-2xl min-w-50">
                    {(models as Model[]).map((m: Model) => (
                      <SelectItem key={m.id} value={m.id} className="rounded-xl py-2 cursor-pointer transition-colors focus:bg-primary/5 focus:text-primary">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold">{m.name}</span>
                          <span className="text-[10px] text-muted-foreground">({m.provider})</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {isProcessing ? (
                <Button
                  onClick={handleStop}
                  size="icon"
                  className="h-8 w-8 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg animate-in zoom-in"
                >
                  <Square size={14} className="fill-current" />
                </Button>
              ) : (
                <Button
                  onClick={handleSend}
                  size="icon"
                  disabled={!input.trim() || disabled}
                  className={cn(
                    "h-8 w-8 rounded-full transition-all shadow-lg",
                    input.trim()
                      ? "bg-primary hover:bg-primary/90 text-primary-foreground scale-100 rotate-0"
                      : "bg-muted text-muted-foreground scale-90 opacity-50"
                  )}
                >
                  <ArrowUp size={18} strokeWidth={2.5} />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
