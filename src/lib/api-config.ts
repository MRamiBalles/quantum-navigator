/**
 * API Configuration for Quantum Navigator Frontend
 * 
 * SECURITY: API keys and URLs are configured via environment variables.
 * In production, set VITE_QUANTUM_API_KEY, VITE_API_BASE_URL, and VITE_WS_BASE_URL.
 * 
 * For local development, the backend runs in insecure dev mode with an ephemeral key.
 */

// API Base URLs - configurable for HTTPS/WSS in production
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

/**
 * Returns the API key from environment variables.
 * In production, VITE_QUANTUM_API_KEY must be set.
 * In development, returns a dev-mode placeholder that the backend will accept.
 */
export function getApiKey(): string {
  const apiKey = import.meta.env.VITE_QUANTUM_API_KEY;
  
  if (!apiKey && import.meta.env.PROD) {
    console.error(
      "[SECURITY] VITE_QUANTUM_API_KEY is not configured. " +
      "API requests will fail in production. " +
      "Set this environment variable before deploying."
    );
    return "";
  }
  
  // In development mode, return a placeholder that dev backend accepts
  return apiKey || "dev-mode";
}

/**
 * Returns standard headers for API requests including authentication.
 */
export function getApiHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-API-Key": getApiKey(),
  };
}

/**
 * Constructs a full API URL for the given endpoint.
 * @param endpoint - API endpoint path (e.g., "/api/favorites/load")
 */
export function apiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`;
}

/**
 * Constructs a full WebSocket URL for the given endpoint.
 * @param endpoint - WebSocket endpoint path (e.g., "/ws/benchmarks/client123")
 */
export function wsUrl(endpoint: string): string {
  return `${WS_BASE_URL}${endpoint}`;
}
