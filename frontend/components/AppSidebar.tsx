'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Map, BarChart3, Settings } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Activity },
  { name: 'Floor Plan', href: '/floorplan', icon: Map },
 {name: 'Stream', href: '/stream', icon: BarChart3 },
];

export default function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-16 bg-surface border-r border-neutral-200 flex flex-col">
      {/* Logo */}
      <div className="h-12 flex items-center justify-center border-b border-neutral-200">
        <div className="w-8 h-8 bg-primary-700 flex items-center justify-center text-white text-xs font-bold">
          TS
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`
                flex flex-col items-center justify-center p-3 transition-colors
                ${isActive 
                  ? 'text-primary-700 bg-primary-50' 
                  : 'text-neutral-500 hover:text-neutral-950 hover:bg-neutral-50'
                }
              `}
              title={item.name}
            >
              <Icon className="w-5 h-5" strokeWidth={1.5} />
              <span className="text-[10px] mt-1 font-light">{item.name.split(' ')[0]}</span>
            </Link>
          );
        })}
      </nav>

      {/* Settings at bottom */}
      <div className="p-3 border-t border-neutral-200">
        <button
          className="w-full flex flex-col items-center justify-center p-2 text-neutral-500 hover:text-neutral-950 transition-colors"
          title="Settings"
        >
          <Settings className="w-5 h-5" strokeWidth={1.5} />
        </button>
      </div>
    </aside>
  );
}
