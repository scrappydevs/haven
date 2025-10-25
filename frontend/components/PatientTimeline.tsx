'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TimelineEvent {
  timestamp: string;
  status: 'NORMAL' | 'CONCERNING' | 'CRITICAL';
  message: string;
  metrics?: {
    heart_rate?: number;
    respiratory_rate?: number;
    crs_score?: number;
    tremor_detected?: boolean;
  };
  reasoning?: string;
  concerns?: string[];
  actions?: string[];
}

interface PatientTimelineProps {
  patientId: string;
  events: TimelineEvent[];
  className?: string;
}

export default function PatientTimeline({ patientId, events, className = '' }: PatientTimelineProps) {
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [timeRange, setTimeRange] = useState(60); // minutes

  // Group events by time intervals (every 5 minutes)
  const groupedEvents = events.reduce((acc, event) => {
    const time = new Date(event.timestamp);
    const intervalKey = Math.floor(time.getTime() / (5 * 60 * 1000)); // 5-minute intervals
    if (!acc[intervalKey]) {
      acc[intervalKey] = [];
    }
    acc[intervalKey].push(event);
    return acc;
  }, {} as Record<number, TimelineEvent[]>);

  // Get most severe event for each interval
  const timelinePoints = Object.entries(groupedEvents).map(([key, eventsInInterval]) => {
    const severityOrder = { 'CRITICAL': 3, 'CONCERNING': 2, 'NORMAL': 1 };
    const mostSevere = eventsInInterval.reduce((prev, current) => {
      return severityOrder[current.status] > severityOrder[prev.status] ? current : prev;
    });
    return {
      intervalKey: parseInt(key),
      event: mostSevere,
      count: eventsInInterval.length
    };
  }).sort((a, b) => a.intervalKey - b.intervalKey);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return 'bg-red-500';
      case 'CONCERNING':
        return 'bg-yellow-500';
      default:
        return 'bg-green-500';
    }
  };

  const getStatusColorLight = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return 'bg-red-100';
      case 'CONCERNING':
        return 'bg-yellow-100';
      default:
        return 'bg-green-100';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const formatTimeShort = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  return (
    <div className={`bg-surface border border-neutral-200 rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-neutral-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-neutral-950 uppercase tracking-wider">
              Patient Status Timeline
            </h3>
            <p className="text-xs font-light text-neutral-500 mt-1">
              Last {timeRange} minutes • {events.length} events
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTimeRange(30)}
              className={`px-3 py-1 text-xs rounded ${
                timeRange === 30 ? 'bg-primary-700 text-white' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
              }`}
            >
              30m
            </button>
            <button
              onClick={() => setTimeRange(60)}
              className={`px-3 py-1 text-xs rounded ${
                timeRange === 60 ? 'bg-primary-700 text-white' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
              }`}
            >
              1h
            </button>
            <button
              onClick={() => setTimeRange(180)}
              className={`px-3 py-1 text-xs rounded ${
                timeRange === 180 ? 'bg-primary-700 text-white' : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
              }`}
            >
              3h
            </button>
          </div>
        </div>
      </div>

      {/* Timeline Visualization */}
      <div className="p-6">
        {timelinePoints.length === 0 ? (
          <div className="text-center py-8 text-neutral-500 text-sm">
            No data available for this time range
          </div>
        ) : (
          <div className="space-y-4">
            {/* Color bar timeline */}
            <div className="relative h-12 bg-neutral-100 rounded-lg overflow-hidden">
              {timelinePoints.map((point, idx) => {
                const width = 100 / timelinePoints.length;
                return (
                  <button
                    key={point.intervalKey}
                    onClick={() => setSelectedEvent(point.event)}
                    className={`absolute h-full ${getStatusColor(point.event.status)} hover:opacity-80 transition-opacity cursor-pointer group`}
                    style={{
                      left: `${idx * width}%`,
                      width: `${width}%`
                    }}
                    title={`${formatTime(point.event.timestamp)} - ${point.event.status}`}
                  >
                    {/* Hover tooltip */}
                    <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                      <div className="bg-neutral-950 text-white px-3 py-2 rounded text-xs whitespace-nowrap">
                        <div className="font-medium">{formatTimeShort(point.event.timestamp)}</div>
                        <div>{point.event.status}</div>
                        {point.count > 1 && <div className="text-neutral-400">{point.count} events</div>}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Time labels */}
            <div className="flex justify-between text-xs text-neutral-500 font-light px-1">
              {timelinePoints.length > 0 && (
                <>
                  <span>{formatTimeShort(timelinePoints[0].event.timestamp)}</span>
                  <span>Now</span>
                </>
              )}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs font-light text-neutral-600 border-t border-neutral-200 pt-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                <span>Normal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span>Concerning</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span>Critical</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Selected Event Details */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-neutral-200 overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-sm font-medium text-neutral-950 mb-1">
                    Event Details
                  </h4>
                  <p className="text-xs text-neutral-500">
                    {formatTime(selectedEvent.timestamp)}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-neutral-500 hover:text-neutral-950 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Status Badge */}
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg mb-4 ${getStatusColorLight(selectedEvent.status)}`}>
                <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedEvent.status)}`}></div>
                <span className={`text-xs font-medium ${
                  selectedEvent.status === 'CRITICAL' ? 'text-red-700' :
                  selectedEvent.status === 'CONCERNING' ? 'text-yellow-700' :
                  'text-green-700'
                }`}>
                  {selectedEvent.status}
                </span>
              </div>

              {/* Message */}
              <div className="mb-4 p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
                <p className="text-sm font-light text-neutral-800">{selectedEvent.message}</p>
              </div>

              {/* Metrics */}
              {selectedEvent.metrics && (
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {selectedEvent.metrics.heart_rate && (
                    <div className="p-3 bg-white border border-neutral-200 rounded-lg">
                      <p className="text-xs text-neutral-500 mb-1">Heart Rate</p>
                      <p className="text-lg font-medium text-neutral-950">{selectedEvent.metrics.heart_rate} bpm</p>
                    </div>
                  )}
                  {selectedEvent.metrics.respiratory_rate && (
                    <div className="p-3 bg-white border border-neutral-200 rounded-lg">
                      <p className="text-xs text-neutral-500 mb-1">Respiratory Rate</p>
                      <p className="text-lg font-medium text-neutral-950">{selectedEvent.metrics.respiratory_rate}/min</p>
                    </div>
                  )}
                  {selectedEvent.metrics.crs_score !== undefined && (
                    <div className="p-3 bg-white border border-neutral-200 rounded-lg">
                      <p className="text-xs text-neutral-500 mb-1">CRS Score</p>
                      <p className="text-lg font-medium text-neutral-950">{(selectedEvent.metrics.crs_score * 100).toFixed(0)}%</p>
                    </div>
                  )}
                  {selectedEvent.metrics.tremor_detected && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-xs text-red-600 mb-1">Tremor Status</p>
                      <p className="text-sm font-medium text-red-700">Detected</p>
                    </div>
                  )}
                </div>
              )}

              {/* AI Reasoning */}
              {selectedEvent.reasoning && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-neutral-600 mb-2">🤖 AI REASONING:</p>
                  <p className="text-sm font-light text-neutral-800 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    {selectedEvent.reasoning}
                  </p>
                </div>
              )}

              {/* Concerns */}
              {selectedEvent.concerns && selectedEvent.concerns.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-neutral-600 mb-2">CONCERNS:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedEvent.concerns.map((concern, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-yellow-50 border border-yellow-200 rounded text-xs font-light text-yellow-800"
                      >
                        {concern}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              {selectedEvent.actions && selectedEvent.actions.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-neutral-600 mb-2">RECOMMENDED ACTIONS:</p>
                  <ul className="space-y-1">
                    {selectedEvent.actions.map((action, idx) => (
                      <li key={idx} className="text-xs font-light text-neutral-700 flex items-start gap-2">
                        <span className="text-neutral-400">•</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

