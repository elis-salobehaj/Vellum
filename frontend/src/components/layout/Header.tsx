import {
  ChevronDown,
  Sparkles,
  Check
} from 'lucide-react';
import { Button } from '@/components/common/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/common/ui/dropdown-menu";

interface HeaderProps {
  selectedModel?: string;
  models: { id: string; name?: string }[];
  onModelChange: (modelId: string) => void;
}

export const Header = ({ selectedModel, models, onModelChange }: HeaderProps) => {
  const currentModel = models.find(m => m.id === selectedModel);

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60 flex items-center justify-between px-4 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-9 px-3 gap-2 font-semibold text-sm hover:bg-accent/50 transition-all rounded-lg">
              <Sparkles size={16} className="text-primary" />
              <span>{currentModel?.name || "Select Model"}</span>
              <ChevronDown size={14} className="text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" sideOffset={10} className="w-56 p-1.5 rounded-xl bg-background! shadow-lg border-border">
            {models.map((model) => (
              <DropdownMenuItem
                key={model.id}
                onClick={() => onModelChange(model.id)}
                className="rounded-lg py-2 cursor-pointer focus:bg-primary/5 focus:text-primary"
              >
                <div className="flex flex-col flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{model.name}</span>
                    {selectedModel === model.id && (
                      <Check size={14} className="text-primary ml-2" />
                    )}
                  </div>
                  <span className="text-[10px] text-muted-foreground">Provider: Enterprise</span>
                </div>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

      </div>

      <div className="flex items-center gap-2">
      </div>
    </header>
  );
};
