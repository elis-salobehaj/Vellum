import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  MessageSquare,
  Settings,
  LogOut,
  Plus,
  User as UserIcon,
  Search,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '@/authConfig';
import { config } from '@/config';
import { logger } from '@/lib/logger';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface HistoryItem {
  id: string;
  title?: string;
}

interface AppSidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const AppSidebar = ({ isCollapsed, setIsCollapsed }: AppSidebarProps) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const navigate = useNavigate();
  const location = useLocation();
  const { instance, accounts } = useMsal();
  const user = accounts[0];

  const fetchHistory = useCallback(async () => {
    try {
      const account = accounts[0];
      let token = "mock-token";

      if (account && !config.auth.bypassAuth) {
        const response = await instance.acquireTokenSilent({
          ...loginRequest,
          account: account
        });
        token = response.idToken;
      }

      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/history/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!res.ok) {
        setHistory([]);
        return;
      }

      const data = await res.json();
      if (Array.isArray(data)) {
        setHistory(data);
      }
    } catch (err) {
      logger.error("sidebar_history_failed", { error: err });
    }
  }, [instance, accounts]);

  useEffect(() => {
    fetchHistory();
  }, [location.pathname, fetchHistory]);

  const handleLogout = () => {
    instance.logoutRedirect({
      postLogoutRedirectUri: "/",
    });
  };

  const getInitials = (name?: string) => {
    if (!name) return "U";
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  return (
    <aside
      className={cn(
        "h-screen bg-background border-r border-border flex flex-col transition-all duration-300 relative z-20",
        isCollapsed ? "w-16" : "w-72"
      )}
    >
      {/* Header */}
      <div className={cn("p-4 flex items-center shrink-0 min-h-[64px]", isCollapsed ? "flex-col gap-2 justify-start" : "justify-between")}>
        {isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-muted-foreground h-8 w-8"
          >
            <PanelLeftOpen size={18} />
          </Button>
        )}

        <div
          onClick={() => navigate('/')}
          className={cn(
            "flex items-center gap-3 overflow-hidden cursor-pointer hover:opacity-80 transition-opacity",
            isCollapsed ? "justify-center" : "justify-start"
          )}
        >
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground shadow-sm shrink-0 font-bold">
            V
          </div>
          {!isCollapsed && (
            <>
              <span className="font-bold text-xl tracking-tight truncate">Vellum</span>
              <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground font-mono">v1.2</span>
            </>
          )}
        </div>

        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-muted-foreground h-8 w-8"
          >
            <PanelLeftClose size={18} />
          </Button>
        )}
      </div>

      <div className="px-3 mb-4 shrink-0">
        <Button
          onClick={() => navigate('/')}
          className={cn(
            "w-full bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl shadow-sm transition-all flex items-center justify-center gap-2",
            isCollapsed ? "h-10 w-10 p-0" : "h-11 px-4"
          )}
        >
          <Plus size={20} />
          {!isCollapsed && <span className="font-medium">New Chat</span>}
        </Button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {!isCollapsed && (
          <div className="px-4 mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest leading-none">History</span>
            <Button variant="ghost" size="icon" className="h-5 w-5 text-muted-foreground hover:text-foreground">
              <Search size={12} />
            </Button>
          </div>
        )}

        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1 py-2">
            {history.length === 0 && !isCollapsed && (
              <div className="px-4 py-8 text-center">
                <p className="text-sm text-muted-foreground italic">No conversations yet</p>
              </div>
            )}

            {history.map((item) => (
              <TooltipProvider key={item.id} delayDuration={500}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={location.pathname === `/chat/${item.id}` ? "secondary" : "ghost"}
                      onClick={() => navigate(`/chat/${item.id}`)}
                      className={cn(
                        "w-full justify-start gap-3 transition-all rounded-lg",
                        isCollapsed ? "px-0 justify-center h-10 w-10 mx-auto" : "h-10 px-3",
                        location.pathname === `/chat/${item.id}` ? "bg-accent text-accent-foreground font-medium" : "text-muted-foreground hover:text-foreground hover:bg-accent/40"
                      )}
                    >
                      <MessageSquare size={18} className="shrink-0" />
                      {!isCollapsed && <span className="truncate">{item.title || "Untitled Chat"}</span>}
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
                    "w-full justify-start gap-3 rounded-lg text-muted-foreground hover:text-foreground",
                    isCollapsed ? "px-0 justify-center h-10 w-10 mx-auto" : "h-10 px-3"
                  )}
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
                "w-full justify-start gap-3 rounded-xl hover:bg-accent/40 p-1.5 transition-colors group",
                isCollapsed ? "h-10 w-10 justify-center mx-auto" : "h-auto px-2"
              )}
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
            <DropdownMenuItem className="rounded-xl py-2 cursor-pointer gap-2 focus:bg-primary/5 focus:text-primary">
              <Settings size={16} /> Preferences
            </DropdownMenuItem>
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
