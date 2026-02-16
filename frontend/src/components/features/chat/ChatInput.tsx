import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Send, Paperclip, Square } from 'lucide-react';
import { Button } from '@/components/common/ui/button';
import { Textarea } from '@/components/common/ui/textarea';
import { cn } from '@/lib/utils';
import { logger } from '@/lib/logger';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isProcessing?: boolean;
  placeholder?: string;
}

export const ChatInput = ({
  onSend,
  onStop,
  disabled = false,
  isProcessing = false,
  placeholder = "Ask anything..."
}: ChatInputProps) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const maxHeight = 200; // Max height in pixels
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send, Shift+Enter for newline
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

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleStop = () => {
    if (onStop) {
      logger.info("chat_generation_stopped");
      onStop();
    }
  };

  return (
    <div className="border-t border-border bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="max-w-3xl mx-auto p-4">
        <div className="relative flex items-end gap-2 bg-background border border-border rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-ring focus-within:border-transparent transition-all">
          {/* Attachment Button */}
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 mb-2 ml-2 text-muted-foreground hover:text-foreground"
            disabled={disabled || isProcessing}
            title="Attach file (coming soon)"
          >
            <Paperclip size={20} />
          </Button>

          {/* Textarea */}
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              "min-h-13 max-h-50 resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 py-3 px-0",
              "placeholder:text-muted-foreground"
            )}
            rows={1}
          />

          {/* Send/Stop Button */}
          <div className="shrink-0 mb-2 mr-2">
            {isProcessing ? (
              <Button
                onClick={handleStop}
                size="icon"
                variant="outline"
                className="rounded-xl"
                title="Stop generating"
              >
                <Square size={18} className="fill-current" />
              </Button>
            ) : (
              <Button
                onClick={handleSend}
                size="icon"
                disabled={!input.trim() || disabled}
                className={cn(
                  "rounded-xl transition-all",
                  input.trim() && !disabled
                    ? "bg-primary hover:bg-primary/90"
                    : "bg-muted text-muted-foreground cursor-not-allowed"
                )}
                title="Send message (Enter)"
              >
                <Send size={18} />
              </Button>
            )}
          </div>
        </div>

        {/* Helper Text */}
        <div className="mt-2 text-xs text-muted-foreground text-center">
          Press <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px] font-mono">Enter</kbd> to send,
          <kbd className="ml-1 px-1.5 py-0.5 bg-muted rounded text-[10px] font-mono">Shift + Enter</kbd> for new line
        </div>
      </div>
    </div>
  );
};
