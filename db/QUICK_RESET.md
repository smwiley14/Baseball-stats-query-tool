# Quick Database Reset

## Simple One-Liner

```bash
psql -h localhost -p 5433 -U baseball -d retrosheet -f db/drop_all.sql && psql -h localhost -p 5433 -U baseball -d retrosheet -f db/init.sql
```

## Or Use the Script

```bash
./scripts/reset_simple.sh
```

## What It Does

1. Drops the entire `public` schema (all tables, views, sequences, etc.)
2. Recreates the `public` schema
3. Runs `init.sql` to recreate all tables

**That's it!** Your database is now clean and reinitialized.
