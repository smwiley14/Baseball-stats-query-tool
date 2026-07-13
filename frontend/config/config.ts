export interface Config {
  apiUrl: string
  environment: 'development' | 'production'
}

const getEnvironment = (): 'development' | 'production' => {
  return import.meta.env.PROD ? 'production' : 'development'
}

const environment = getEnvironment()

// Resolve the API base path. In production it is derived at RUNTIME from where
// index.html is actually mounted (document.baseURI), so one build works both at
// a dedicated domain's root ("/" -> "/api") and under the portfolio subpath
// ("/baseball/" -> "/baseball/api") with no rebuild per hostname. The frontend
// Nginx's `location /api/` proxies to the backend either way.
// NOTE: relies on a trailing slash at the mount point (e.g. /baseball/, not
// /baseball) — the reverse proxy must redirect the bare path. See DEPLOY.md.
const resolveApiBase = (): string => {
  // An explicit build-time override always wins (e.g. a cross-origin API host).
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  // Dev goes through the Vite proxy, which injects X-API-Key (see vite.config.ts).
  if (import.meta.env.DEV) return '/api'
  // Production: resolve "api" against the document base -> /api or /baseball/api.
  return new URL('api', document.baseURI).pathname
}

const configs: Record<'development' | 'production', Config> = {
  development: { apiUrl: resolveApiBase(), environment: 'development' },
  production: { apiUrl: resolveApiBase(), environment: 'production' },
}

export const config: Config = configs[environment]

// Helper to get full API endpoint URL
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  const base = config.apiUrl.replace(/\/$/, '')
  return `${base}/${cleanEndpoint}`
}

// Log config in development (useful for debugging)
if (environment === 'development') {
  console.log('🔧 Configuration:', config)
}