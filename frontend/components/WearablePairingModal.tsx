'use client';

import { useState, useEffect } from 'react';
import { getApiUrl } from '@/lib/api';

interface WearablePairingModalProps {
  isOpen: boolean;
  patientId: string;
  onClose: () => void;
  onPaired: () => void;
}

export default function WearablePairingModal({
  isOpen,
  patientId,
  onClose,
  onPaired
}: WearablePairingModalProps) {
  const [pairingCode, setPairingCode] = useState<string>('');
  const [deviceId, setDeviceId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [isPaired, setIsPaired] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen && !pairingCode) {
      initiatePairing();
    }

    // Cleanup when modal closes
    return () => {
      if (!isOpen) {
        setPairingCode('');
        setDeviceId('');
        setIsPaired(false);
        setError('');
      }
    };
  }, [isOpen]);

  const initiatePairing = async () => {
    setIsLoading(true);
    setError('');

    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/wearable/pair/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId })
      });

      if (!response.ok) {
        throw new Error('Failed to initiate pairing');
      }

      const data = await response.json();
      setPairingCode(data.pairing_code);
      setDeviceId(data.device_id);
      setExpiresAt(new Date(data.expires_at));

      // Start polling for pairing completion
      pollForPairing(data.pairing_code);
    } catch (err) {
      console.error('Error initiating pairing:', err);
      setError('Failed to generate pairing code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const pollForPairing = async (code: string) => {
    const interval = setInterval(async () => {
      try {
        const apiUrl = getApiUrl();
        const response = await fetch(`${apiUrl}/wearable/pair/status/${code}`);

        if (!response.ok) {
          console.error('Failed to check pairing status');
          return;
        }

        const data = await response.json();

        if (data.status === 'active') {
          setIsPaired(true);
          clearInterval(interval);

          // Wait 2 seconds before closing
          setTimeout(() => {
            onPaired();
            onClose();
          }, 2000);
        }
      } catch (err) {
        console.error('Error checking pairing status:', err);
      }
    }, 2000); // Poll every 2 seconds

    // Stop polling after 5 minutes (code expires)
    setTimeout(() => {
      clearInterval(interval);
      if (!isPaired) {
        setError('Pairing code expired. Please try again.');
      }
    }, 300000);
  };

  const getTimeRemaining = () => {
    if (!expiresAt) return '';

    const now = new Date();
    const diffMs = expiresAt.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 1000 / 60);
    const diffSecs = Math.floor((diffMs / 1000) % 60);

    if (diffMs <= 0) return 'Expired';

    return `${diffMins}:${diffSecs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-surface border-2 border-neutral-950 p-8 max-w-md w-full mx-4">
        {/* Header */}
        <div className="border-b-2 border-neutral-950 pb-4 mb-6">
          <h2 className="text-lg font-medium uppercase tracking-wider text-neutral-950">
            Pair Apple Watch
          </h2>
          <p className="text-xs text-neutral-600 mt-1">Patient: {patientId}</p>
        </div>

        {/* Content */}
        {error ? (
          // Error State
          <div className="text-center py-8">
            <div className="text-4xl mb-4 text-red-500">⚠️</div>
            <p className="text-neutral-700 mb-4">{error}</p>
            <button
              onClick={initiatePairing}
              className="px-6 py-2 border border-primary-700 text-primary-700 hover:bg-primary-700 hover:text-white transition-all text-xs uppercase tracking-wider"
            >
              Try Again
            </button>
          </div>
        ) : isPaired ? (
          // Success State
          <div className="text-center py-8">
            <div className="text-6xl mb-4 text-green-500">✓</div>
            <p className="text-neutral-700 font-medium">Device paired successfully!</p>
            <p className="text-xs text-neutral-500 mt-2">Vitals streaming will begin shortly...</p>
          </div>
        ) : isLoading ? (
          // Loading State
          <div className="text-center py-8">
            <div className="animate-spin h-8 w-8 border-2 border-neutral-300 border-t-neutral-950 rounded-full mx-auto mb-4"></div>
            <p className="text-neutral-600 text-sm">Generating pairing code...</p>
          </div>
        ) : (
          // Pairing Code Display
          <>
            <div className="text-center py-8">
              <p className="text-neutral-600 mb-4 text-sm">
                Enter this code on the Apple Watch:
              </p>

              {/* Large Pairing Code */}
              <div className="bg-neutral-50 border-2 border-neutral-300 py-6 mb-4">
                <div className="text-6xl font-mono font-bold text-primary-700 tracking-widest">
                  {pairingCode}
                </div>
              </div>

              {/* Expiration Timer */}
              {expiresAt && (
                <div className="flex items-center justify-center gap-2 text-xs text-neutral-500">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Expires in {getTimeRemaining()}</span>
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="mt-6 space-y-3 text-xs text-neutral-600 bg-neutral-50 border border-neutral-200 p-4">
              <p className="font-medium text-neutral-950 mb-2">Instructions:</p>
              <p className="flex items-start gap-2">
                <span className="text-primary-700 font-mono">1.</span>
                Open Haven app on Apple Watch
              </p>
              <p className="flex items-start gap-2">
                <span className="text-primary-700 font-mono">2.</span>
                Enter the 6-digit code shown above
              </p>
              <p className="flex items-start gap-2">
                <span className="text-primary-700 font-mono">3.</span>
                Watch will start streaming vitals automatically
              </p>
            </div>

            {/* Waiting Indicator */}
            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-neutral-500">
              <div className="animate-pulse">●</div>
              <span>Waiting for watch to pair...</span>
            </div>
          </>
        )}

        {/* Footer */}
        <div className="mt-8 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-neutral-300 hover:border-neutral-950 transition-colors text-xs uppercase tracking-wider"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
