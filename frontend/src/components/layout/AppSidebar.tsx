import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Settings,
  SunMoon,
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
import { SidebarItem } from '@/components/layout/SidebarItem';

import { useAuth } from '@/hooks/useAuth';
import { useChatHistory } from '@/hooks/useChatHistory';
import type { ChatSession } from '@/types/index';
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
        "h-screen bg-background/95 backdrop-blur-sm flex flex-col shrink-0 transition-[width,transform] ease-in-out border-r border-border/10",
        isCollapsed
          ? "w-16 translate-x-0"
          : "w-70 translate-x-0 origin-left"
      )}
      aria-label="Sidebar Navigation"
    >
      {/* Header */}
      <div className="flex bg-background/50 backdrop-blur-sm relative transition-all h-16 flex-row items-center justify-between px-4">
        {/* Logo Container - Bottom when collapsed (order-2) */}
        {!isCollapsed && (
          <div
            className="flex items-center gap-3 overflow-hidden transition-all order-1"
          >
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center text-primary-foreground shadow-sm shrink-0 font-bold">
              V
            </div>
            <div className="flex items-center gap-2 overflow-hidden animate-in fade-in slide-in-from-left-2 ">
              <span className="font-bold text-xl tracking-tight truncate">Vellum</span>
            </div>
          </div>
        )}

        {/* Toggle Button - Top when collapsed (order-1) */}
        <Button
          variant="ghost"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            "text-muted-foreground transition-all hover:bg-accent/40 hover:scale-105 active:scale-95 order-1 rounded-lg bg-accent/10",
            isCollapsed ? "w-full" : "w-fit"
          )}
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isCollapsed ? "Expand sidebar (ctrl+[ )" : "Collapse sidebar (ctrl+[ )"}
        >
          <PanelLeft />
        </Button>
      </div>

      <div className="px-4 mb-4">
        <Button
          onClick={() => navigate('/')}
          className={cn(
            "w-full bg-primary transition-all text-primary-foreground rounded-lg hover:scale-105 active:scale-95",
          )}
          aria-label="New Chat"
          title="New Chat (ctrl+i)"
        >
          <Plus />
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

        <ScrollArea className="px-1">
          {!isCollapsed && (
            <div className="px-2 pb-2 pt-2">
              {history.map((item: ChatSession) => (
                <SidebarItem
                  key={item.id}
                  item={item}
                  isActive={location.pathname === `/chat/${item.id}`}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Footer */}
      <div className="p-2 shrink-0 space-y-1">

        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                asChild
                variant="ghost"
                className={cn(
                  "w-full justify-start gap-3 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/40 active:scale-95 transition-all",
                  isCollapsed ? "px-0 justify-center h-10 w-10 mx-auto" : "h-10 px-3"
                )}
                aria-label="Admin Settings"
              >
                <Link to="/admin">
                  <Settings className="shrink-0" />
                  {!isCollapsed && <span className="font-medium">Admin Settings</span>}
                </Link>
              </Button>
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
                <SunMoon size={16} /> Appearance
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
