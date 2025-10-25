'use client';

import { Bell } from 'lucide-react';

export default function AppHeader() {
  return (
    <header className="h-12 border-b border-neutral-200 bg-surface px-6 flex items-center justify-end">
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative p-2 text-neutral-500 hover:text-neutral-950 transition-colors">
          <Bell className="w-4 h-4" strokeWidth={1.5} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        {/* User avatar */}
        <div className="w-7 h-7 rounded-full bg-neutral-200 flex items-center justify-center text-neutral-600 text-xs font-medium">
          U
        </div>
      </div>
    </header>
  );
}

