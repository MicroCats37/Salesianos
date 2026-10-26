import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from modules.salesianos_fest.domain.models import PaquetePrecio, Paquete
from django.db.models import Count
from django.utils import timezone

total = PaquetePrecio.objects.count()
activos = PaquetePrecio.objects.filter(activo=True).count()
inactivos = PaquetePrecio.objects.filter(activo=False).count()
con_vigente_hasta = PaquetePrecio.objects.exclude(vigente_hasta__isnull=True).count()
con_vigente_hasta_null = PaquetePrecio.objects.filter(vigente_hasta__isnull=True).count()
por_paquete = Paquete.objects.annotate(n=Count("precios")).values("nombre", "n").order_by("nombre")

print(f"TOTAL precios: {total}")
print(f"  activos: {activos}")
print(f"  inactivos: {inactivos}")
print(f"  con vigente_hasta: {con_vigente_hasta}")
print(f"  con vigente_hasta NULL: {con_vigente_hasta_null}")
print()
print("PRECIOS POR PAQUETE:")
for p in por_paquete:
    print(f"  {p['nombre'][:30]:30} → {p['n']} precio(s)")
print()
print(f"Hoy: {timezone.now().date()}")