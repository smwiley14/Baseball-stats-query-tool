# Production Deployment

This deploys the Docker Compose stack (Postgres + FastAPI backend + Nginx
frontend) on a single VPS, behind a reverse proxy you already run. TLS/domain
can be added to that proxy later.

The three services bind to `127.0.0.1` only (5433 Postgres, 8000 backend,
3000 frontend). Nothing is exposed to the internet directly — your reverse
proxy is the only public entry point, and it should target the **frontend**
container on `127.0.0.1:3000`. The frontend's own Nginx proxies `/api` to the
backend internally, so you never expose 8000 or 5433 publicly.

---

## 1. Before the first boot (on the server)

### a. Put the data dump in place
Copy your `pg_dump` to `db/retrosheet.sql`. On a **fresh** Postgres volume the
init scripts run automatically in order and set everything up:

```
00 enable pgvector → 01 load retrosheet.sql → 02 readonly user
→ 03 views → 04 vector-store tables → 05 materialize aggregate views
```

So a clean first boot loads the data AND builds the materialized views — no
manual steps. (The materialized-view build can take a few minutes on the full
dataset; that's expected.)

### b. Create `backend/.env` (gitignored — must be created on the server)
Copy `backend/.env.example` and fill it in. Critical values:

```
API_KEY=<64-char random hex — generate: openssl rand -hex 32>

POSTGRES_HOST=postgres          # Docker service name, NOT localhost
POSTGRES_PORT=5432              # internal port, NOT 5433
POSTGRES_USER=baseball          # keep 'baseball' so it matches dump ownership
POSTGRES_PASSWORD=<strong random password>   # NOT 'baseball'
POSTGRES_DB=retrosheet
POSTGRES_DATABASE=retrosheet
POSTGRES_READONLY_USER=baseball_app
POSTGRES_READONLY_PASSWORD=<strong random password>

OPENAI_API_KEY=<your key>
LANGCHAIN_TRACING_V2=false      # or true with a LANGCHAIN_API_KEY if you want traces
ALLOWED_ORIGINS=               # leave blank until you have a domain (see §5)
```

### c. Create `frontend/.env` (gitignored)
It only needs **one** line, and it **must match** `backend/.env`'s `API_KEY`
exactly:

```
API_KEY=<same value as backend/.env>
```

> **Why this matters:** the backend rejects any request without the right
> `X-API-Key`. The frontend's Nginx injects that header server-side from
> `frontend/.env`. If the two `API_KEY` values differ, every query returns 401.

---

## 2. First deploy

```bash
docker compose up -d --build --remove-orphans
docker compose logs -f backend        # watch until "Application startup complete"
docker compose ps                     # all three should be (healthy)
```

First backend startup also embeds the knowledge base via OpenAI (one-time on a
fresh DB), so give it a minute before it reports healthy.

---

## 3. Serve it both at the portfolio `/baseball` AND at its own domain

The frontend build is **mount-agnostic**: assets use relative paths and the API
path is resolved at runtime from wherever `index.html` is served (see
`frontend/config/config.ts`). So **one build/container serves both** — your
existing `portfolio.com/baseball` and a new dedicated hostname at its root — with
no rebuild per hostname. Just point two reverse-proxy vhosts at the same
`127.0.0.1:3000`.

Rebuild the frontend once to pick up the relative-base build:

```bash
docker compose up -d --build frontend
```

### 3a. Keep the portfolio subpath (`portfolio.com/baseball`)

Same prefix-stripping proxy as before — but the trailing-slash redirect is now
**required** (relative assets need the document URL to end in `/`):

```nginx
# in your portfolio's server block
location = /baseball { return 301 /baseball/; }   # REQUIRED now, not optional
location /baseball/ {
    proxy_pass http://127.0.0.1:3000/;            # trailing slash strips /baseball/
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 3b. Add the dedicated site (its own hostname, served at root)

1. **DNS:** point the hostname at the droplet — an `A` record to the droplet IP
   (a subdomain like `baseball.<yourdomain>` is easiest; you already control that
   zone). 
2. **New server block** (served at root, so **no** prefix-stripping):

   ```nginx
   server {
       server_name baseball.example.com;      # your chosen hostname
       # ... your usual listen / TLS lines (see §5 for certs) ...
       location / {
           proxy_pass http://127.0.0.1:3000;   # NO trailing slash-strip needed
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. **TLS:** issue a cert for the new hostname (e.g. `certbot --nginx -d
   baseball.example.com`), or extend whatever your portfolio already uses.

Both URLs now serve the same app: `portfolio.com/baseball/` and
`https://baseball.example.com/`. (Caddy/Traefik: same idea — subpath vhost strips
`/baseball`, root vhost doesn't.)

---

## 4. Verify

```bash
# From the server, straight at the container:
curl -s http://127.0.0.1:3000/            # should return index.html
# Through your proxy:
curl -s http://<server-ip>/baseball/      # index.html
# Full workflow (the smoke test hits the frontend's /api proxy):
BASE_URL=http://127.0.0.1:3000/api ./scripts/smoke_test.sh
```

All 11 smoke-test checks should pass.

---

## 5. Security / cost must-dos (do these before sharing the URL)

- **Strong DB password** — set `POSTGRES_PASSWORD` to a random value (§1b). It's
  localhost-bound so not internet-reachable, but the fresh volume bakes it in
  permanently, so set it right the first time.
- **Cap OpenAI spend** — the site has **no user login**; anyone who can reach the
  URL can run queries (rate-limited to 10/min per IP by the frontend Nginx), and
  every query makes OpenAI calls. Set a hard monthly usage limit in the OpenAI
  dashboard. If you don't want it open to the public at all, gate `/baseball/`
  behind your reverse proxy's auth (basic auth / SSO).
- **`ALLOWED_ORIGINS`** — once you add a domain, set it to that origin in
  `backend/.env` (e.g. `https://stats.example.com`) and restart the backend.
  Until then, requests are same-origin through the proxy so CORS isn't hit.

---

## 6. Ongoing operations

- **Updating code:** `git pull && docker compose up -d --build`. Config-only
  changes to `configs/` or `backend/configs/` need the backend rebuilt (they're
  baked into the image), plus a one-off knowledge-base refresh:
  `docker compose exec -T -e FORCE_REINIT_KNOWLEDGE_BASE=true backend \
   python3 -c "from knowledge.init.init_vector_store import init_knowledge_base; init_knowledge_base()"`
- **After loading new baseball data:** re-run `db/refresh_materialized_views.sh`
  so leaderboards/career totals pick it up (materialized views don't auto-update).
- **If you change a materialized-view *definition*** (not just data): re-run the
  full `db/05-materialize-views.sh` inside the postgres container.
- **Backups:** the DB is fully reproducible from `db/retrosheet.sql` + the init
  scripts, so a lost volume isn't catastrophic. The only non-reproducible data is
  the accumulated "learned" query examples in `langchain_pg_embedding`; back up
  the `postgres_data` volume if you want to preserve those.
