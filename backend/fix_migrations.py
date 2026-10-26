import sys
sys.path.insert(0, '.')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from django.db import connection
from datetime import datetime

cursor = connection.cursor()

# Check current state
cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('admin', 'usuarios', 'auth') ORDER BY id")
print("Current migrations:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Delete incorrect admin.0001_initial record
cursor.execute("DELETE FROM django_migrations WHERE app = 'admin' AND name = '0001_initial'")
print(f"Deleted admin.0001_initial: {cursor.rowcount} rows")

# Insert usuarios.0001_initial as fake-applied
now = datetime.now()
cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('usuarios', '0001_initial', ?)", (now,))
print(f"Inserted fake usuarios.0001_initial")

connection.commit()
print("Done - now run: uv run python manage.py migrate --settings=config.settings.development")
