# Baseball Stats Query Tool - Frontend

A simple React TypeScript frontend for the Baseball Stats Query Tool.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables (optional):
   - For local development, the default API URL is `http://localhost:8000`
   - To override, create a `.env.local` file in the root directory:
   ```bash
   VITE_API_URL=http://localhost:8000
   ```
   - For production, create a `.env.production` file:
   ```bash
   VITE_API_URL=https://your-production-api.com
   ```

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Environment Configuration

The app uses Vite's environment variables. The configuration is managed in `config/config.ts`:

- **Development**: Uses `http://localhost:8000` by default (or `VITE_API_URL` from `.env.development` or `.env.local`)
- **Production**: Uses the value from `VITE_API_URL` environment variable (set during build)

### Environment Files

- `.env.development` - Development environment variables (committed to git)
- `.env.production` - Production environment variables (committed to git)
- `.env.local` - Local overrides (not committed to git, add to `.gitignore`)

### Setting Production API URL

For production builds, set the `VITE_API_URL` environment variable:

```bash
VITE_API_URL=https://api.yourdomain.com npm run build
```

Or create a `.env.production` file with your production API URL.

## Build

To build for production:
```bash
npm run build
```

The built files will be in the `dist` directory.

## Preview Production Build

To preview the production build:
```bash
npm run preview
```
