# Docker Compose Setup

This docker-compose setup automatically initializes the PostgreSQL database with the comprehensive schema.

## Quick Start

1. **Start the database:**
   ```bash
   docker-compose up -d
   ```

2. **Verify the schema was created:**
   ```bash
   docker exec -it retrosheet-postgres psql -U baseball -d retrosheet -c "\dt"
   ```

3. **Load your data:**
   ```bash
   ./db/load_data.sh
   ./db/load_events.sh  # Optional, for play-by-play events
   ```

## What Gets Initialized

When the container starts for the first time, PostgreSQL automatically runs all `.sql` files in `/docker-entrypoint-initdb.d/` in alphabetical order:

- `01-schema.sql` - Creates all tables, indexes, and views

## Accessing the Database

### Command Line (psql)
```bash
# Connect to the database
docker exec -it retrosheet-postgres psql -U baseball -d retrosheet

# Or from your host machine
psql -h localhost -p 5433 -U baseball -d retrosheet
```

### pgAdmin (Web Interface)
1. Open http://localhost:5051 in your browser
2. Login with:
   - Email: `admin@admin.com`
   - Password: `admin`
3. Add a new server:
   - Host: `postgres` (or `localhost` if connecting from host)
   - Port: `5432` (or `5433` if connecting from host)
   - Database: `retrosheet`
   - Username: `baseball`
   - Password: `baseball`

## Resetting the Database

If you need to start fresh:

```bash
# Stop and remove containers and volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

**Warning:** This will delete all data! Make sure to backup first if needed.

## Environment Variables

You can customize the database setup by creating a `.env` file:

```env
POSTGRES_USER=baseball
POSTGRES_PASSWORD=baseball
POSTGRES_DB=retrosheet
POSTGRES_PORT=5433
```

## Data Persistence

Data is stored in a Docker volume named `postgres_data`. This means:
- Data persists even if you stop the container
- Data is removed only if you use `docker-compose down -v`
- To backup: `docker exec retrosheet-postgres pg_dump -U baseball retrosheet > backup.sql`
- To restore: `docker exec -i retrosheet-postgres psql -U baseball retrosheet < backup.sql`

## Troubleshooting

### Schema not created
If the schema wasn't created on first startup:
1. Check logs: `docker-compose logs postgres`
2. Ensure `db/schema.sql` exists and is readable
3. Remove volumes and restart: `docker-compose down -v && docker-compose up -d`

### Connection issues
- Verify container is running: `docker ps`
- Check port mapping: `docker-compose ps`
- Test connection: `docker exec -it retrosheet-postgres psql -U baseball -d retrosheet -c "SELECT 1;"`

### Permission issues
- Ensure `db/schema.sql` has read permissions: `chmod 644 db/schema.sql`


