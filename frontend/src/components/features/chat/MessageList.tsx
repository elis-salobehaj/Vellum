import { useEffect, useRef, useState } from 'react';
import { ArrowDown } from 'lucide-react';
import { Button } from '@/components/common/ui/button';
import { cn } from '@/lib/utils';
import type { Citation as ICitation } from '@/types';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: ICitation[];
}

interface MessageListProps {
  messages: Message[];
  isProcessing: boolean;
  children: React.ReactNode;
}

export const MessageList = ({ messages, isProcessing, children }: MessageListProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isNearBottom, setIsNearBottom] = useState(true);

  const scrollToBottom = (smooth = true) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      });
    }
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // Show button if user scrolled up more than 200px from bottom
    setShowScrollButton(distanceFromBottom > 200);
    setIsNearBottom(distanceFromBottom < 100);
  };

  // Auto-scroll when new messages arrive (only if user is near bottom)
  useEffect(() => {
    if (isNearBottom) {
      scrollToBottom(true);
    }
  }, [messages, isProcessing, isNearBottom]);

  // Scroll to bottom on initial mount
  useEffect(() => {
    scrollToBottom(false);
  }, []);

  return (
    <div className="relative flex-1 overflow-hidden">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="h-full overflow-y-auto scroll-smooth"
      >
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
          {children}
        </div>
      </div>

      {/* Scroll to Bottom Button */}
      <div
        className={cn(
          "absolute bottom-4 left-1/2 -translate-x-1/2 transition-all duration-200",
          showScrollButton ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2 pointer-events-none"
        )}
      >
        <Button
          variant="outline"
          size="icon"
          onClick={() => scrollToBottom(true)}
          className="rounded-full shadow-lg bg-background hover:bg-accent border-border"
        >
          <ArrowDown size={18} />
        </Button>
      </div>
    </div>
  );
};
