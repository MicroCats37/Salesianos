import os, sys, django
from pathlib import Path

# Allow running from temp dir
sys.path.insert(0, r"C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from modules.salesianos_fest.domain.models import PaquetePrecio
from django.utils import timezone

sys.stdout.reconfigure(encoding="utf-8")

precios = PaquetePrecio.objects.filter(activo=True).order_by("paquete__nombre", "vigente_desde")
print(f"Total active precios: {precios.count()}")
print("=" * 100)
for p in precios:
    hoy = timezone.now().date()
    realmente_vigente = p.vigente_desde <= hoy and (p.vigente_hasta is None or p.vigente_hasta >= hoy)
    lo_que_retorna_el_backend = PaquetePrecio.objects.filter(paquete_id=p.paquete_id, activo=True).order_by("-vigente_desde").first()
    backend_devuelve_este = lo_que_retorna_el_backend.pk == p.pk
    print(f"  {p.paquete.nombre[:30]:30} | etapa={p.etapa:10} | desde={p.vigente_desde} hasta={p.vigente_hasta} | S/{p.precio_unitario}")
    print(f"    >> realmente_vigente_hoy={realmente_vigente} | backend_devuelve_este={backend_devuelve_este}")
print("=" * 100)
print(f"Hoy es: {timezone.now().date()}")