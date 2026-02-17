import { useNavigate } from 'react-router-dom';
import {
  MoreVertical,
  Pin,
  Pencil,
  Trash2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/common/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/common/ui/dropdown-menu";
import type { ChatSession } from '@/types/index';

interface SidebarItemProps {
  item: ChatSession;
  isActive: boolean;
}

export const SidebarItem = ({ item, isActive }: SidebarItemProps) => {
  const navigate = useNavigate();

  const handleAction = (e: React.MouseEvent, action: string) => {
    e.stopPropagation();
    // TODO: Implement actual actions
    console.log(`Action: ${action} on ${item.id}`);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "w-full flex items-center justify-start relative group rounded-4xl transition-all h-9 px-2 cursor-pointer",
        isActive
          ? "bg-accent/60 text-accent-foreground font-medium shadow-sm"
          : "text-muted-foreground hover:bg-accent/40 hover:text-foreground"
      )}
      onClick={() => navigate(`/chat/${item.id}`)}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/chat/${item.id}`)}
    >
      <span className={cn(
        "truncate text-sm flex-1 text-left",
        isActive ? "text-primary" : "text-muted-foreground/70"
      )}
      >{item.title || "Untitled Chat"}</span>

      {/* Context Menu Trigger - Visible only on hover or when menu is open */}
      <div className="absolute right-0 opacity-0 rounded-4xl group-hover:opacity-100 transition-opacity group-hover:bg-accent shadow-xl" onClick={(e) => e.stopPropagation()}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="secondary"
              size="icon"
              className="h-8 w-8 rounded-4xl"
            >
              <MoreVertical size={14} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40 rounded-xl p-1 shadow-lg bg-background/95 backdrop-blur-lg">
            <DropdownMenuItem
              onClick={(e) => handleAction(e, 'pin')}
              className="gap-2 text-xs font-medium rounded-lg cursor-pointer"
            >
              <Pin size={14} /> Pin Chat
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => handleAction(e, 'rename')}
              className="gap-2 text-xs font-medium rounded-lg cursor-pointer"
            >
              <Pencil size={14} /> Rename
            </DropdownMenuItem>
            <DropdownMenuSeparator className="opacity-50" />
            <DropdownMenuItem
              onClick={(e) => handleAction(e, 'delete')}
              className="gap-2 text-xs font-medium rounded-lg cursor-pointer text-destructive focus:bg-destructive/10 focus:text-destructive"
            >
              <Trash2 size={14} /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};
