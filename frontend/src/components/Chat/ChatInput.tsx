import { useState, useRef, useEffect } from 'react';
import { Send, Plus, Maximize2, Minimize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const ChatInput = ({ onSend, disabled }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height

      // Dynamic Height Limits
      const maxHeight = isMaximized ? window.innerHeight * 0.6 : 300;

      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [input, isMaximized]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      if (isMaximized) {
        setIsMaximized(false);
      } else {
        setIsFocused(false);
        textareaRef.current?.blur();
      }
    }
  };

  const handleSend = () => {
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput('');
    setIsFocused(false);
    setIsMaximized(false);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const toggleMaximize = () => {
    setIsMaximized(!isMaximized);
    if (!isFocused) setIsFocused(true);
    textareaRef.current?.focus();
  };

  const handleBackdropClick = () => {
    setIsMaximized(false);
  };

  return (
    <>
      {/* Backdrop for click-outside */}
      {isMaximized && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-[2px] z-40 transition-opacity duration-200"
          onClick={handleBackdropClick}
        />
      )}

      {/* Input Container */}
      <motion.div
        // Removed 'layout' prop to prevent layout thrashing/glitches
        initial={{ y: 0 }}
        animate={{
          y: 0,
          scale: 1,
          // Width Logic: Always 100% of parent, MaxWidth toggles
          maxWidth: isMaximized ? "100%" : "48rem", // 48rem = max-w-3xl
          boxShadow: (isFocused || isMaximized)
            ? "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
            : "0 1px 2px 0 rgb(0 0 0 / 0.05)"
        }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className={clsx(
          "relative z-50 mx-auto bg-white border rounded-2xl transition-colors",
          (isFocused || isMaximized) ? "border-blue-400 ring-2 ring-blue-50" : "bg-gray-50 border-gray-200 hover:border-gray-300",
          // Fallback width class
          "w-full"
        )}
      >
        <div className="flex gap-2 p-3">

          {/* Attachment Button */}
          <div className="flex items-end self-end">
            <button
              className="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition-colors mb-0.5"
              title="Add attachment"
            >
              <Plus size={20} />
            </button>
          </div>

          {/* Text Area */}
          <div className="flex-1 py-1">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              className={clsx(
                "w-full bg-transparent border-none outline-none focus:outline-none focus:ring-0 focus:border-none text-base resize-none custom-scrollbar leading-relaxed",
                // Min heights
                isMaximized ? "min-h-[40vh]" : "min-h-[48px] max-h-[300px]"
              )}
              rows={1}
              disabled={disabled}
            />
          </div>

          {/* Right Column: Buttons */}
          <div className="flex flex-col justify-between items-center min-h-[48px] h-auto">
            {/* Maximize Button */}
            <button
              onClick={toggleMaximize}
              className="text-gray-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              title={isMaximized ? "Minimize" : "Deep drafting mode"}
            >
              {isMaximized ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </button>

            {/* Send Button */}
            <button
              className={clsx(
                "p-2 rounded-xl transition-all duration-200 shadow-sm mt-auto",
                input.trim() && !disabled
                  ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md"
                  : "bg-gray-200 text-gray-400 cursor-not-allowed"
              )}
              onClick={handleSend}
              disabled={!input.trim() || disabled}
            >
              <Send size={18} />
            </button>
          </div>

        </div>

        {/* Helper Text */}
        <AnimatePresence>
          {isMaximized && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="px-4 pb-3 text-xs text-gray-400 flex justify-between border-t border-gray-100 pt-2 mx-2"
            >
              <span>Use Shift + Enter for new line</span>
              <span>Drafting Canvas Active</span>
            </motion.div>
          )}
        </AnimatePresence>

      </motion.div>
    </>
  );
};

export default ChatInput;
