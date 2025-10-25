/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

/**
 * Get the backend API URL
 * Works in both development and production
 */
export function getApiUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/, '');
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    // Allow overriding the port without requiring the full URL
    const port = process.env.NEXT_PUBLIC_API_PORT || '8000';
    const apiProtocol = protocol === 'https:' ? 'https:' : 'http:';
    return `${apiProtocol}//${hostname}:${port}`;
  }

  // Server-side fallback (build-time)
  return 'http://localhost:8000';
}

/**
 * Get the WebSocket URL with optional path
 * Converts http to ws protocol
 * @param path Optional path to append (e.g., '/ws/stream/P-001')
 */
export function getWsUrl(path?: string): string {
  const apiUrl = getApiUrl();
  try {
    const url = new URL(apiUrl);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';

    if (path) {
      // Ensure we don't end up with a double slash when appending paths
      url.pathname = `${url.pathname.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
    }

    return url.toString();
  } catch {
    // Fallback for legacy strings
    const baseWsUrl = apiUrl.replace(/^http/i, 'ws');
    return path ? `${baseWsUrl}${path}` : baseWsUrl;
  }
}

// Export constants for convenience
export const API_URL = getApiUrl();
export const WS_URL = getWsUrl();
