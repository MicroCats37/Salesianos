import os, sys, django, json
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
c = Client()
r = c.get('/api/inscripciones/5208d884-9925-4d30-85b5-cede31828fd2/detalle')
data = r.json()
for eq in data['data']['equipos']:
    print('---')
    print('nombre:', eq.get('nombre'))
    print('estado_roster:', eq.get('estado_roster'))
    print('estado_equipo:', eq.get('estado_equipo'))
    print('jugadores_registrados:', eq.get('jugadores_registrados'))
    print('minimo_deportivo:', eq.get('minimo_deportivo'))
    print('faltantes:', eq.get('faltantes'))
    print('participantes (count):', len(eq.get('participantes', [])))