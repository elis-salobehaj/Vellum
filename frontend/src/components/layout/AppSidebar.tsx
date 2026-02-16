import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  MessageSquare,
  Settings,
  LogOut,
  Plus,
  User as UserIcon,
  PanelLeft,
  Sun,
  Moon,
  Laptop,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/common/ui/button';
import { ScrollArea } from '@/components/common/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
} from "@/components/common/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/common/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/common/ui/tooltip";

import { useAuth } from '@/hooks/useAuth';
import { useChatHistory, type ChatSession } from '@/hooks/useChatHistory';
import { useTheme } from '@/components/providers/theme/ThemeProvider';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

interface AppSidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const AppSidebar = ({ isCollapsed, setIsCollapsed }: AppSidebarProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  const { data: history = [] } = useChatHistory();

  useKeyboardShortcuts({
    'mod+i': () => navigate('/'),
    'mod+[': () => setIsCollapsed(!isCollapsed),
  });

  const handleLogout = () => {
    logout();
  };

  const getInitials = (name?: string) => {
    if (!name) return "U";
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  return (
    <aside
      className={cn(
        "h-screen bg-background border-r border-border flex flex-col transition-all duration-300 relative z-20",
        isCollapsed ? "w-17.5" : "w-70"
      )}
      aria-label="Sidebar Navigation"
    >
      {/* Header */}
      <div className={cn(
        "flex shrink-0 border-b border-border/50 bg-background/50 backdrop-blur-sm relative transition-all duration-300",
        isCollapsed ? "h-32 flex-col items-center justify-center gap-4 px-0" : "h-16 flex-row items-center justify-between px-4"
      )}>
        {/* Logo Container - Bottom when collapsed (order-2) */}
        <div
          className={cn(
            "flex items-center gap-3 overflow-hidden transition-all duration-300",
            isCollapsed ? "order-2 justify-center" : "order-1"
          )}
        >
          <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center text-primary-foreground shadow-sm shrink-0 font-bold">
            V
          </div>
          {!isCollapsed && (
            <div className="flex items-center gap-2 overflow-hidden animate-in fade-in slide-in-from-left-2 duration-300">
              <span className="font-bold text-xl tracking-tight truncate">Vellum</span>
            </div>
          )}
        </div>

        {/* Toggle Button - Top when collapsed (order-1) */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            "text-muted-foreground transition-all duration-300 hover:bg-accent/40 hover:scale-105 active:scale-95 order-1 h-12 w-12 rounded-2xl bg-accent/10",
          )}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isCollapsed ? "Expand sidebar (ctrl+[ )" : "Collapse sidebar (ctrl+[ )"}
        >
          <PanelLeft size={20} />
        </Button>
      </div>

      <div className="px-3 mb-4 shrink-0 mt-4">
        <Button
          onClick={() => navigate('/')}
          className={cn(
            "w-full bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl shadow-sm transition-all flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98]",
            isCollapsed ? "h-10 w-10 p-0" : "h-11 px-4"
          )}
          aria-label="New Chat"
          title="New Chat (ctrl+i)"
        >
          <Plus size={20} />
          {!isCollapsed && <span className="font-medium">New Chat</span>}
        </Button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-hidden flex flex-col min-h-0">
        {!isCollapsed && (
          <div className="px-4 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center justify-between">
            <span>Recent Chats</span>
          </div>
        )}

        <ScrollArea className="flex-1 px-3">
          <div className="space-y-1 pb-4">
            {history.map((item: ChatSession) => (
              <TooltipProvider key={item.id} delayDuration={500}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={location.pathname === `/chat/${item.id}` ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 relative group rounded-xl transition-all",
                        isCollapsed ? "h-10 w-10 p-0 justify-center" : "h-10 px-3",
                        location.pathname === `/chat/${item.id}`
                          ? "bg-accent text-accent-foreground font-medium shadow-sm"
                          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                      )}
                      onClick={() => navigate(`/chat/${item.id}`)}
                    >
                      <MessageSquare size={18} className="shrink-0" />
                      {!isCollapsed && (
                        <span className="truncate text-sm">{item.title || "Untitled Chat"}</span>
                      )}
                    </Button>
                  </TooltipTrigger>
                  {isCollapsed && (
                    <TooltipContent side="right">
                      {item.title || "Untitled Chat"}
                    </TooltipContent>
                  )}
                </Tooltip>
              </TooltipProvider>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="p-2 shrink-0 space-y-1">

        <TooltipProvider delayDuration={500}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Link to="/admin">
                <Button
                  variant="ghost"
                  className={cn(
                    "w-full justify-start gap-3 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/40 active:scale-95 transition-all",
                    isCollapsed ? "px-0 justify-center h-10 w-10 mx-auto" : "h-10 px-3"
                  )}
                  aria-label="Admin Settings"
                >
                  <Settings size={18} className="shrink-0" />
                  {!isCollapsed && <span className="font-medium">Admin Settings</span>}
                </Button>
              </Link>
            </TooltipTrigger>
            {isCollapsed && <TooltipContent side="right">Admin Settings</TooltipContent>}
          </Tooltip>
        </TooltipProvider>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-3 rounded-xl hover:bg-accent/40 p-1.5 transition-all group active:scale-[0.98]",
                isCollapsed ? "h-10 w-10 justify-center mx-auto" : "h-auto px-2"
              )}
              aria-label="User Account Menu"
            >
              <Avatar className="h-8 w-8 border-2 border-primary/10 group-hover:border-primary/30 transition-all">
                <AvatarImage src="" />
                <AvatarFallback className="bg-primary/5 text-primary text-xs font-bold">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>

              {!isCollapsed && (
                <div className="flex flex-col items-start overflow-hidden py-0.5">
                  <span className="text-sm font-semibold truncate w-full text-foreground group-hover:text-primary transition-colors">{user?.name || "Guest User"}</span>
                  <span className="text-[10px] text-muted-foreground truncate w-full">{user?.username || "authenticated"}</span>
                </div>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56 mb-2 ml-2 p-1.5 rounded-2xl shadow-2xl border-border/50 backdrop-blur-xl bg-background/95" align="end" side={isCollapsed ? "right" : "top"}>
            <DropdownMenuLabel className="font-semibold text-xs text-muted-foreground px-2 py-1.5 uppercase tracking-wider">My Account</DropdownMenuLabel>
            <DropdownMenuSeparator className="opacity-50" />

            <DropdownMenuItem className="rounded-xl py-2 cursor-pointer gap-2 focus:bg-primary/5 focus:text-primary">
              <UserIcon size={16} /> Profile
            </DropdownMenuItem>

            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="rounded-xl py-2 cursor-pointer gap-2 focus:bg-primary/5 focus:text-primary">
                <Settings size={16} /> Appearance
              </DropdownMenuSubTrigger>
              <DropdownMenuPortal>
                <DropdownMenuSubContent className="p-1.5 rounded-2xl shadow-2xl border-border/50 backdrop-blur-xl bg-background/95 min-w-37.5">
                  <DropdownMenuItem onClick={() => setTheme("light")} className="rounded-xl py-2 cursor-pointer gap-2 justify-between">
                    <div className="flex items-center gap-2">
                      <Sun size={14} /> Light
                    </div>
                    {theme === "light" && <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-medium">Active</span>}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setTheme("dark")} className="rounded-xl py-2 cursor-pointer gap-2 justify-between">
                    <div className="flex items-center gap-2">
                      <Moon size={14} /> Dark
                    </div>
                    {theme === "dark" && <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-medium">Active</span>}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setTheme("system")} className="rounded-xl py-2 cursor-pointer gap-2 justify-between">
                    <div className="flex items-center gap-2">
                      <Laptop size={14} /> System
                    </div>
                    {theme === "system" && <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-medium">Active</span>}
                  </DropdownMenuItem>
                </DropdownMenuSubContent>
              </DropdownMenuPortal>
            </DropdownMenuSub>

            <DropdownMenuSeparator className="opacity-50" />
            <DropdownMenuItem
              onClick={handleLogout}
              className="rounded-xl py-2 cursor-pointer gap-2 text-destructive focus:bg-destructive/10 focus:text-destructive font-medium"
            >
              <LogOut size={16} /> Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
};
