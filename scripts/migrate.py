#!/usr/bin/env python3
"""Apply versioned SQL migrations."""
import os, glob
from backend.db import execute, get_conn

def applied():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("SELECT version FROM schema_migrations")
            return {r[0] for r in cur.fetchall()}

def main():
    done = applied()
    for path in sorted(glob.glob("database/migrations/*.sql")):
        ver = os.path.basename(path)
        if ver in done:
            print(f"skip {ver}")
            continue
        sql = open(path).read()
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (ver,))
        print(f"applied {ver}")

if __name__ == "__main__":
    main()
