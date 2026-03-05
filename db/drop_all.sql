-- Simple script to drop everything in the public schema
-- Run: psql -d retrosheet -f db/drop_all.sql

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO baseball;
GRANT ALL ON SCHEMA public TO public;
