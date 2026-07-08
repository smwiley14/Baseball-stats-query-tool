export interface Config {
  apiUrl: string
  environment: 'development' | 'production'
}

const getEnvironment = (): 'development' | 'production' => {
  return import.meta.env.PROD ? 'production' : 'development'
}

const environment = getEnvironment()

const configs: Record<'development' | 'production', Config> = {
  development: {
    // Relative path so requests go through the Vite dev server's /api proxy
    // (see vite.config.ts), which injects X-API-Key. Hitting the backend's
    // absolute http://localhost:8000 directly skips that proxy entirely and
    // the backend rejects the request with 401 for lacking the key.
    apiUrl: import.meta.env.VITE_API_URL || '/api',
    environment: 'development',
  },
  production: {
    apiUrl: import.meta.env.VITE_API_URL || '/baseball/api',
    environment: 'production',
  },
}

export const config: Config = configs[environment]

// Helper to get full API endpoint URL
export const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${config.apiUrl}/${cleanEndpoint}`
}

// Log config in development (useful for debugging)
if (environment === 'development') {
  console.log('🔧 Configuration:', config)
}