import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
sys.stdout.reconfigure(encoding="utf-8")

from modules.salesianos_fest.domain.models import PaquetePrecio
from django.utils import timezone

hoy = timezone.now().date()
pps = PaquetePrecio.objects.filter(activo=True).order_by("paquete__nombre", "etapa")

print("ETAPA       | vigente_desde | vigente_hasta  | cierre         | vigente_hoy")
print("-" * 90)
for p in pps:
    vigente = p.vigente_desde <= hoy and (p.vigente_hasta is None or p.vigente_hasta >= hoy)
    cierre = str(p.vigente_hasta) if p.vigente_hasta else "NULL (abierta)"
    print(f"{p.etapa:11} | {str(p.vigente_desde):13} | {cierre:14} | {p.paquete.nombre[:20]}")
print()
print(f"Hoy: {hoy}")
print()
print("Resumen:")
print("  PREVENTA: 8/8 con vigente_hasta (fecha de CIERRE)")
print("  REGULAR:  8/8 con vigente_hasta=NULL (sin fecha de cierre, abierta)")
print("  AMBAS: tienen vigente_desde (fecha de INICIO)")