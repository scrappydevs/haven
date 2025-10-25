'use client';

import { usePathname } from 'next/navigation';

export default function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b-2 border-neutral-950 bg-surface">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo */}
          <div>
            <h1 className="text-3xl font-playfair font-black text-primary-950 leading-tight">
              Haven
            </h1>
          </div>

          {/* Center: Navigation */}
          <nav className="flex items-center gap-1">
            <a
              href="/dashboard"
              className={`px-6 py-2 label-uppercase text-xs transition-colors ${
                pathname === '/dashboard'
                  ? 'text-neutral-950 border-b-2 border-primary-700'
                  : 'text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50'
              }`}
            >
              Dashboard
            </a>
            <a
              href="/dashboard/floorplan"
              className={`px-6 py-2 label-uppercase text-xs transition-colors ${
                pathname === '/dashboard/floorplan'
                  ? 'text-neutral-950 border-b-2 border-primary-700'
                  : 'text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50'
              }`}
            >
              Floor Plan
            </a>
            <a
              href="/stream"
              className={`px-6 py-2 label-uppercase text-xs transition-colors ${
                pathname === '/stream'
                  ? 'text-neutral-950 border-b-2 border-primary-700'
                  : 'text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50'
              }`}
            >
              Stream
            </a>
          </nav>

          {/* Right side: Alerts & User */}
          <div className="flex items-center gap-4">
            {/* Notifications */}
            <button className="relative p-2 text-neutral-500 hover:text-neutral-950 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {/* User avatar */}
            <div className="w-9 h-9 rounded-full bg-neutral-200 border border-neutral-300 flex items-center justify-center text-neutral-600 text-sm font-medium">
              U
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

