# GEMINI.md - Project Guidelines & Data Protection Mandates

## Data Persistence & Safety Guarantee
- **Zero Data Loss Policy:** Never perform destructive database operations (such as `DROP TABLE`, `DELETE FROM` without conditions, or overwriting `.db` files).
- **Idempotent Migrations:** All database schema updates must be purely additive (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN ...` wrapped in `try...except sqlite3.OperationalError`).
- **Persistent Storage:** Always use persistent paths (`DATABASE_PATH` / `/data/community_database.db`) for SQLite databases and user uploads.
