import os, sys, django, json
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
c = Client()
r = c.get('/api/inscripciones/5208d884-9925-4d30-85b5-cede31828fd2/detalle')
data = r.json()
print('Equipo[0] keys:', list(data['data']['equipos'][0].keys()))
print('Equipo[0] full:')
print(json.dumps(data['data']['equipos'][0], indent=2, default=str)[:1500])