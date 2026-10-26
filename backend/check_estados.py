import os, sys, django, json
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
c = Client()
r = c.get('/api/inscripciones/5208d884-9925-4d30-85b5-cede31828fd2/detalle')
data = r.json()
for eq in data['data']['equipos'][:1]:
    print('Equipo:', eq['nombre'])
    for p in eq.get('participantes', []):
        print(f'  - {p["persona"]["nombres"]} {p["persona"]["apellidos"]} | estado={p["estado"]}')