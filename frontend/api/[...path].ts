// Vercel serverless proxy (Node runtime).
//
// The frontend is a static site, so it cannot safely hold the API key. This
// function runs on Vercel's servers instead: the browser calls it same-origin
// (/api/*  -> no CORS), and it forwards the request to the backend VPS with the
// X-API-Key header attached from a SERVER-SIDE env var that the browser never
// sees.
//
// Required Vercel Environment Variables (Project -> Settings -> Environment
// Variables). Do NOT prefix these with VITE_ — that would inline them into the
// public browser bundle and defeat the whole point:
//   BACKEND_URL   e.g. https://api.batgpt.samwiley-stuff.com
//   API_KEY       the same value as the backend's API_KEY
//
// This assumes the Vercel project's Root Directory is `frontend/`, so this file
// lives at <root>/api/ and handles every /api/* path. If your Vercel root is the
// repo root instead, move this file to /api/[...path].ts there.

// Long NL2SQL queries can take a while; give the function room (subject to your
// Vercel plan's max — Hobby caps lower, so very slow queries may still time out).
export const config = { maxDuration: 60 }

export default async function handler(req: any, res: any) {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.API_KEY
  if (!backendUrl || !apiKey) {
    res.status(500).json({ detail: 'Proxy misconfigured: set BACKEND_URL and API_KEY in Vercel.' })
    return
  }

  // Strip the /api prefix: /api/chat -> /chat, /api/chat/cancel -> /chat/cancel.
  // req.url includes the path (and any query string).
  const path = String(req.url || '').replace(/^\/api/, '') || '/'
  const target = backendUrl.replace(/\/+$/, '') + path

  let body: string | undefined
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    // Vercel parses JSON bodies into objects; re-serialize for the upstream call.
    body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {})
  }

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers: {
        'Content-Type': (req.headers['content-type'] as string) || 'application/json',
        'X-API-Key': apiKey,
      },
      body,
    })
    const text = await upstream.text()
    res.status(upstream.status)
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json')
    res.send(text)
  } catch {
    res.status(502).json({ detail: 'Upstream request failed.' })
  }
}
