/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// Get API URL - client-side only
export const API_URL = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

// Function to get API URL (for compatibility)
export const getApiUrl = () => API_URL;

// WebSocket URL (convert http to ws)
export const WS_URL = API_URL.replace('http', 'ws');

// Function to get WebSocket URL with optional path
export const getWsUrl = (path?: string) => {
  const baseWsUrl = API_URL.replace('http', 'ws');
  return path ? `${baseWsUrl}${path}` : baseWsUrl;
};
