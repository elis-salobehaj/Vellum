import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { cn } from '@/lib/utils';

export const AppLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(true);

  return (
    <div className="flex h-screen bg-background overflow-hidden selection:bg-primary/10">
      <AppSidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />

      <main className={cn(
        "flex-1 flex flex-col min-h-0 overflow-hidden transition-all relative",
        // Gradient overlay for depth
        "after:absolute after:inset-0 after:pointer-events-none after:bg-[radial-gradient(circle_at_top_right,var(--tw-gradient-stops))] after:from-primary/5 after:via-transparent after:to-transparent"
      )}>
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
