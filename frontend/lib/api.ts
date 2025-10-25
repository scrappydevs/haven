/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

/**
 * Get the backend API URL
 * Works in both development and production
 */
export function getApiUrl(): string {
  // In production (Vercel), use environment variable
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // In development, use localhost
  return 'http://localhost:8000';
}

/**
 * Get the WebSocket URL
 * Converts http to ws protocol
 */
export function getWsUrl(): string {
  const apiUrl = getApiUrl();
  return apiUrl.replace('http', 'ws');
}

// Export constants for convenience
export const API_URL = getApiUrl();
export const WS_URL = getWsUrl();

