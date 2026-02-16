import { MessageSquare, FileSearch, Lightbulb, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface EmptyStateProps {
  onSuggestionClick: (suggestion: string) => void;
}

const suggestions = [
  {
    icon: FileSearch,
    title: "Summarize my documents",
    prompt: "Can you summarize the key points from my uploaded documents?"
  },
  {
    icon: MessageSquare,
    title: "Find information about...",
    prompt: "Help me find information about specific topics in my knowledge base"
  },
  {
    icon: Lightbulb,
    title: "Answer a question",
    prompt: "I have a question about the content in my documents"
  },
  {
    icon: Sparkles,
    title: "Analyze data",
    prompt: "Can you analyze and provide insights from my data?"
  }
];

export const EmptyState = ({ onSuggestionClick }: EmptyStateProps) => {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-3xl w-full space-y-8">
        {/* Logo and Tagline */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl shadow-lg">
            <span className="text-3xl font-bold text-primary-foreground">V</span>
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome to Vellum</h1>
            <p className="text-muted-foreground mt-2">
              Your intelligent knowledge assistant. Ask me anything about your documents.
            </p>
          </div>
        </div>

        {/* Suggestion Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestions.map((suggestion, index) => {
            const Icon = suggestion.icon;
            return (
              <Card
                key={index}
                onClick={() => onSuggestionClick(suggestion.prompt)}
                className="p-4 cursor-pointer hover:bg-accent/50 transition-all hover:shadow-md border-border group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                    <Icon size={20} className="text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm mb-1">{suggestion.title}</h3>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {suggestion.prompt}
                    </p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Helpful Tip */}
        <div className="text-center text-sm text-muted-foreground">
          <p>Tip: Press <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono">Shift + Enter</kbd> for a new line</p>
        </div>
      </div>
    </div>
  );
};
