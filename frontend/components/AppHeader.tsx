'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import AlertsModal from './AlertsModal';

interface Alert {
  id?: string;
  alert_type: string;
  severity: string;
  patient_id?: string;
  room_id?: string;
  title: string;
  description?: string;
  status: string;
  triggered_at: string;
  metadata?: any;
}

interface AppHeaderProps {
  alerts?: Alert[];
  onAlertResolve?: (alertId: string) => void;
  onPatientClick?: (patientId: number) => void;
  onManualAlertsClick?: () => void;
}

export default function AppHeader({ alerts = [], onAlertResolve, onPatientClick, onManualAlertsClick }: AppHeaderProps) {
  const pathname = usePathname();
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  
  const activeAlertsCount = alerts.filter(a => a.status === 'active').length;

  return (
    <header className="border-b-2 border-neutral-950 bg-surface">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo */}
          <Link href="/" className="cursor-pointer">
            <h1 className="text-lg font-light text-neutral-950 uppercase tracking-wider hover:text-primary-700 transition-colors">
              Haven
            </h1>
          </Link>

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
              href="/patient-view"
              className={`px-6 py-2 label-uppercase text-xs transition-colors ${
                pathname === '/patient-view'
                  ? 'text-neutral-950 border-b-2 border-primary-700'
                  : 'text-neutral-600 hover:text-neutral-950 hover:bg-neutral-50'
              }`}
            >
              Patient View
            </a>
          </nav>

          {/* Right side: Alerts & User */}
          <div className="flex items-center gap-4">
            {/* Manual Alerts Button - Only show on dashboard */}
            {pathname === '/dashboard' && onManualAlertsClick && (
              <button
                onClick={onManualAlertsClick}
                className="px-4 py-2 text-xs font-medium uppercase tracking-wide border border-neutral-300 rounded-full text-neutral-700 hover:text-neutral-950 hover:border-neutral-950 transition-colors"
              >
                Manual Alerts
              </button>
            )}
            
            {/* Notifications */}
            <button 
              onClick={() => setShowAlertsModal(true)}
              className="relative p-2 text-neutral-500 hover:text-neutral-950 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              {activeAlertsCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">
                  {activeAlertsCount}
                </span>
              )}
            </button>

            {/* User avatar */}
            <div className="w-9 h-9 rounded-full bg-neutral-200 border border-neutral-300 flex items-center justify-center text-neutral-600 text-sm font-medium">
              U
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Modal */}
      <AlertsModal
        isOpen={showAlertsModal}
        onClose={() => setShowAlertsModal(false)}
        alerts={alerts}
        onAlertResolve={onAlertResolve}
        onPatientClick={onPatientClick}
      />
    </header>
  );
}

