import clsx from 'clsx';
import { User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    id: string;
    source: string;
    page: number;
    text: string;
  }>;
}

interface MessageBubbleProps {
  message: Message;
  onCitationClick: (citation: any) => void;
}

const MessageBubble = ({ message, onCitationClick }: MessageBubbleProps) => {
  const isUser = message.role === 'user';

  return (
    <div className={clsx("flex gap-4 max-w-3xl mx-auto p-4", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isUser ? "bg-gray-200" : "bg-blue-600 text-white"
      )}>
        {isUser ? <User size={16} /> : <div className="text-xs font-bold">AI</div>}
        {/* <Bot size={16} /> */}
      </div>

      <div className={clsx("flex-1 space-y-2", isUser && "text-right")}>
        <div className={clsx(
          "inline-block rounded-2xl px-5 py-3 text-sm leading-relaxed text-left",
          // text-left ensures markdown doesn't get right-aligned weirdly if user sends long md
          isUser ? "bg-gray-100 text-gray-800" : "bg-white border border-gray-100 shadow-sm text-gray-800 w-full"
        )}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-h1:text-lg prose-h2:text-base prose-p:text-gray-800 prose-a:text-blue-600 hover:prose-a:underline prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-50">
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {message.citations && message.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2 not-prose">
              {message.citations.map((c, i) => (
                <div key={i} className="flex items-center gap-1 rounded-md bg-blue-50 border border-blue-100 overflow-hidden hover:bg-blue-100 transition-colors">
                  <a
                    href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/files/${c.source}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-2 py-1 text-blue-700 text-xs flex items-center gap-1 hover:underline"
                  >
                    [{i + 1}] {c.source}
                  </a>
                  <button
                    onClick={() => onCitationClick(c)}
                    className="px-1 py-1 text-blue-400 hover:text-blue-600 border-l border-blue-100"
                    title="View Preview"
                  >
                    <span className="sr-only">Preview</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
