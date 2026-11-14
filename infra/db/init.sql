-- Database roles for one database on a WeLinc PostgreSQL server (VRMS spec 0008, Database roles).
-- Run as the server admin, once per database, before its first migration. infra/scripts/db-init.sh
-- runs it for all seven with the passwords from the private file:
--
--   psql "<admin url>/postgres" -v db=vrms -v owner_pw=... -v app_pw=... \
--        -v extensions=vector,pg_trgm -f infra/db/init.sql
--
-- Safe to run again: it creates what is missing and resets the two passwords. It grants only
-- through default privileges, never on tables that exist already, so a rerun can never undo the
-- audit_logs revoke that backend-vrms's migration job applies (spec 0021).

\set ON_ERROR_STOP on
\set owner :db '_owner'
\set app :db '_app'

-- The two roles: <db>_owner runs migrations and owns every table, <db>_app is what the service
-- connects as (no DDL, so it can't drop or alter a table)
SELECT format('CREATE ROLE %I LOGIN', :'owner')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'owner') \gexec
SELECT format('CREATE ROLE %I LOGIN', :'app')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app') \gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'owner', :'owner_pw') \gexec
SELECT format('ALTER ROLE %I PASSWORD %L', :'app', :'app_pw') \gexec

-- PostgreSQL 16: the admin is no superuser, so it must be a member of the owner role to hand it
-- the database and to set default privileges for it
SELECT format('GRANT %I TO CURRENT_USER', :'owner') \gexec

SELECT format('ALTER DATABASE %I OWNER TO %I', :'db', :'owner') \gexec

-- Seven databases share one server: only this database's roles may connect to it
SELECT format('REVOKE CONNECT, TEMPORARY ON DATABASE %I FROM PUBLIC', :'db') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'db', :'app') \gexec

\connect :db

-- PostgreSQL 16 lets only the schema owner create in public
SELECT format('ALTER SCHEMA public OWNER TO %I', :'owner') \gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'app') \gexec

-- Tables and sequences that later migrations create (as the owner) are open to the app
SELECT format(
  'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
  :'owner', :'app') \gexec
SELECT format(
  'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO %I',
  :'owner', :'app') \gexec

-- Extensions the server allows (azure.extensions, set by Bicep) are created here as the admin:
-- vector and pg_trgm on vrms. The migrations' own CREATE EXTENSION IF NOT EXISTS then finds them.
SELECT format('CREATE EXTENSION IF NOT EXISTS %I', e)
FROM unnest(string_to_array(:'extensions', ',')) AS e
WHERE e <> '' \gexec
