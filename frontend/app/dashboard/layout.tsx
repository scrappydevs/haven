'use client';

import { usePathname } from 'next/navigation';
import AppHeader from '@/components/AppHeader';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  
  // Hide AppHeader on main dashboard page (it has its own custom header with navigation)
  const showAppHeader = pathname !== '/dashboard';

  return (
    <div className="flex flex-col h-screen w-full bg-background overflow-hidden">
      {/* Header - only show on sub-pages, not main dashboard */}
      {showAppHeader && <AppHeader />}
      
      {/* Page Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

