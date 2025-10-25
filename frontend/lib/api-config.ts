/**
 * API Configuration
 * Centralized configuration for backend API endpoints
 */

// Get API URL - client-side only
export const API_URL = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

// WebSocket URL (convert http to ws)
export const WS_URL = API_URL.replace('http', 'ws');
