import { type CSSProperties, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, RotateCw, Download } from 'lucide-react';
import { Button } from '@/components/common/ui/button';
import { Badge } from '@/components/common/ui/badge';
import { config } from '@/config/index';
import type { Citation as ICitation } from '@/types';

interface AssistantMessageProps {
  content: string;
  citations?: ICitation[];
  onRegenerate?: () => void;
}

export const AssistantMessage = ({ content, citations, onRegenerate }: AssistantMessageProps) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [copiedMessage, setCopiedMessage] = useState(false);

  const handleCopyCode = async (code: string, language: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(language);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleCopyMessage = async () => {
    await navigator.clipboard.writeText(content);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  return (
    <div className="flex gap-4 group">
      {/* Avatar */}
      <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0 shadow-sm">
        <span className="text-primary-foreground font-bold text-sm">V</span>
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0 space-y-3">
        {/* Markdown Content */}
        <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-h1:text-xl prose-headings:text-foreground prose-h2:text-lg prose-h3:text-base prose-p:text-foreground prose-p:leading-relaxed prose-a:text-primary hover:prose-a:underline prose-strong:text-foreground prose-code:text-primary prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-code:before:content-none prose-code:after:content-none prose-pre:bg-transparent prose-pre:p-0 prose-ul:my-2 prose-ol:my-2 prose-li:text-foreground">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkBreaks]}
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                const codeString = String(children).replace(/\n$/, '');
                const isCodeBlock = !!match;

                if (isCodeBlock) {
                  return (
                    <div className="relative group/code my-4">
                      <div className="flex items-center justify-between bg-muted/50 border border-border rounded-t-lg px-4 py-2">
                        <span className="text-xs font-mono text-muted-foreground">{language}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyCode(codeString, language)}
                          className="h-7 px-2 text-xs opacity-0 group-hover/code:opacity-100 transition-opacity"
                        >
                          {copiedCode === language ? (
                            <>
                              <Check size={14} className="mr-1" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy size={14} className="mr-1" />
                              Copy
                            </>
                          )}
                        </Button>
                      </div>
                      <SyntaxHighlighter
                        style={oneDark as { [key: string]: CSSProperties }}
                        language={language}
                        PreTag="div"
                        className="mt-0! rounded-t-none! rounded-b-lg! my-0! border border-t-0 border-border"
                      >
                        {codeString}
                      </SyntaxHighlighter>
                    </div>
                  );
                }

                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Citations */}
        {citations && citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {citations.map((citation, i) => (
              <a
                key={i}
                href={`${config.apiUrl}/files/${citation.source}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 group/citation"
              >
                <Badge variant="outline" className="bg-primary/5 border-primary/20 hover:bg-primary/10 transition-colors">
                  <Download size={12} className="mr-1 opacity-60" />
                  <span className="text-xs">[{i + 1}] {citation.source}</span>
                </Badge>
              </a>
            ))}
          </div>
        )}

        {/* Action Toolbar */}
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopyMessage}
            className="h-7 px-2 text-xs"
          >
            {copiedMessage ? (
              <>
                <Check size={14} className="mr-1" />
                Copied
              </>
            ) : (
              <>
                <Copy size={14} className="mr-1" />
                Copy
              </>
            )}
          </Button>
          {onRegenerate && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRegenerate}
              className="h-7 px-2 text-xs"
            >
              <RotateCw size={14} className="mr-1" />
              Regenerate
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
