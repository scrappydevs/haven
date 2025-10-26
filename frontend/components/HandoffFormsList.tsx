'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';
import HandoffFormModal from './HandoffFormModal';

interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  patient_id: string;
  room_id?: string;
  title: string;
  description?: string;
  status: string;
  triggered_at: string;
  metadata?: any;
  created_at: string;
}

interface HandoffFormsListProps {
  limit?: number;
  refreshInterval?: number; // in milliseconds
}

export default function HandoffFormsList({ limit = 10, refreshInterval = 5000 }: HandoffFormsListProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchAlerts();

    // Set up auto-refresh
    const interval = setInterval(fetchAlerts, refreshInterval);
    return () => clearInterval(interval);
  }, [limit, refreshInterval]);

  const fetchAlerts = async () => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/alerts?status=active&limit=${limit}`);
      const data = await response.json();
      setAlerts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAlertClick = (alertId: string) => {
    setSelectedAlertId(alertId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedAlertId(null);
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'border-red-500 bg-red-50',
      high: 'border-orange-500 bg-orange-50',
      medium: 'border-yellow-500 bg-yellow-50',
      low: 'border-green-500 bg-green-50',
      info: 'border-blue-500 bg-blue-50',
    };
    return colors[severity.toLowerCase()] || 'border-neutral-300 bg-neutral-50';
  };

  const getSeverityBadge = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-neutral-900',
      low: 'bg-green-500 text-white',
      info: 'bg-blue-500 text-white',
    };
    return colors[severity.toLowerCase()] || 'bg-neutral-500 text-white';
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <>
      <div className="bg-surface border border-neutral-200 h-full flex flex-col overflow-hidden rounded-lg">
        {/* Header */}
        <div className="px-6 py-4 border-b-2 border-neutral-950 flex-shrink-0">
          <h2 className="text-sm font-medium uppercase tracking-wider text-neutral-950">
            Active Alerts
          </h2>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="px-6 py-4 h-full overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-neutral-500">
                  <div className="animate-spin h-4 w-4 border-2 border-neutral-300 border-t-neutral-950 rounded-full mx-auto"></div>
                </div>
              </div>
            ) : alerts.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-neutral-500">
                  <p className="text-sm font-light">No active alerts</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <AnimatePresence>
                  {alerts.map((alert, idx) => (
                    <motion.button
                      key={alert.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.2, delay: idx * 0.05 }}
                      onClick={() => handleAlertClick(alert.id)}
                      className={`w-full text-left p-3 border-2 transition-all cursor-pointer shadow-sm hover:shadow-md ${
                        alert.severity.toLowerCase() === 'critical'
                          ? 'border-red-500 bg-red-50 hover:bg-red-100'
                          : alert.severity.toLowerCase() === 'high'
                          ? 'border-orange-500 bg-orange-50 hover:bg-orange-100'
                          : alert.severity.toLowerCase() === 'medium'
                          ? 'border-yellow-500 bg-yellow-50 hover:bg-yellow-100'
                          : 'border-blue-500 bg-blue-50 hover:bg-blue-100'
                      }`}
                    >
                      {/* Header: Severity badge + Time */}
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          alert.severity.toLowerCase() === 'critical'
                            ? 'bg-red-600 text-white'
                            : alert.severity.toLowerCase() === 'high'
                            ? 'bg-orange-600 text-white'
                            : alert.severity.toLowerCase() === 'medium'
                            ? 'bg-yellow-600 text-white'
                            : 'bg-blue-600 text-white'
                        }`}>
                          {alert.severity}
                        </span>
                        <span className="text-[10px] text-neutral-500">
                          {getTimeAgo(alert.triggered_at)}
                        </span>
                      </div>

                      {/* Alert Title */}
                      <div className="text-sm font-medium text-neutral-950 mb-1">
                        {alert.title}
                      </div>

                      {/* Patient + Alert Type */}
                      <div className="flex items-center gap-2 text-[10px] text-neutral-600">
                        <span className="font-medium">{alert.patient_id}</span>
                        <span>•</span>
                        <span className="uppercase tracking-wide">{alert.alert_type.replace('_', ' ')}</span>
                      </div>
                    </motion.button>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      <HandoffFormModal
        formId={selectedAlertId}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onAcknowledge={fetchAlerts} // Refresh list when acknowledged
      />
    </>
  );
}
