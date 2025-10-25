'use client';

import { Bell } from 'lucide-react';

interface AppHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export default function AppHeader({ title, subtitle, actions }: AppHeaderProps) {
  return (
    <header className="h-12 border-b border-neutral-200 bg-surface px-6 flex items-center justify-between">
      <div className="flex items-baseline gap-3">
        <h1 className="text-lg font-light text-neutral-950">{title}</h1>
        {subtitle && (
          <span className="text-xs text-neutral-500 font-light">{subtitle}</span>
        )}
      </div>
      
      <div className="flex items-center gap-4">
        {actions}
        
        {/* Notifications */}
        <button className="relative p-2 text-neutral-500 hover:text-neutral-950 transition-colors">
          <Bell className="w-4 h-4" strokeWidth={1.5} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        {/* User avatar */}
        <div className="w-7 h-7 rounded-full bg-primary-700 flex items-center justify-center text-white text-xs font-medium">
          TS
        </div>
      </div>
    </header>
  );
}

