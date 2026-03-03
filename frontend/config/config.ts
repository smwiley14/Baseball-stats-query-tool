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
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    environment: 'development',
  },
  production: {
    apiUrl: import.meta.env.VITE_API_URL || 'https://api.example.com',
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