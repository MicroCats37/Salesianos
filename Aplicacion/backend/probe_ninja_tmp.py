import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ.setdefault("NINJA_SKIP_REGISTRY", "1")
import django
django.setup()
from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja import Schema
from pydantic import Field

class In(Schema):
    titulo: str = Field(..., min_length=1)

@api_controller("/probe")
class Probe:
    @route.post("/a", response={200: dict})
    async def a(self, request, payload: In):
        return {}

api = NinjaExtraAPI(urls_namespace="probe-x")
api.register_controllers(Probe)
from django.test import Client
c = Client()
r = c.post("/probe/a", data="{}", content_type="application/json")
print("STATUS", r.status_code)
print("BODY", r.content[:800])
