# import_gtfs.py
# Importe les données GTFS TCL dans une base SQLite locale.
# Usage : python3 import_gtfs.py [dossier_gtfs]
# Par défaut, cherche les fichiers .txt dans le répertoire courant.

import sqlite3
import csv
import os
import sys

GTFS_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcl.db")

# shapes.txt inutile pour les horaires (tracé géo des lignes), ignoré
TABLES = [
    "agency", "routes", "trips", "stops",
    "stop_times", "calendar", "calendar_dates",
    "transfers", "fare_attributes", "fare_rules"
]

print(f"Source GTFS : {GTFS_DIR}")
print(f"Base SQLite : {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

for table in TABLES:
    path = os.path.join(GTFS_DIR, f"{table}.txt")
    if not os.path.exists(path):
        print(f"⚠ {table}.txt absent, ignoré")
        continue
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(f'CREATE TABLE "{table}" ({col_defs})')
        placeholder = ",".join("?" * len(cols))
        batch = []
        count = 0
        for row in reader:
            batch.append(list(row.values()))
            if len(batch) == 10000:
                conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholder})', batch)
                count += len(batch)
                batch = []
        if batch:
            conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholder})', batch)
            count += len(batch)
        conn.commit()
        print(f"✓ {table} ({count} lignes)")

print("\nCréation des index...")
conn.execute("CREATE INDEX IF NOT EXISTS idx_st_trip     ON stop_times(trip_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_st_stop     ON stop_times(stop_id, departure_time)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_route   ON trips(route_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_trips_service ON trips(service_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_stops_name    ON stops(stop_name)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_service    ON calendar_dates(service_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_date       ON calendar_dates(date)")
conn.commit()
conn.close()
print("✓ Done — tcl.db prêt")
