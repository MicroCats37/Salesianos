"""Fixtures compartidas del núcleo (A0).

`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3: el `conftest.py` de un nivel
SOLO importa y registra los módulos de fixtures; las fixtures reales viven en
`fixtures/`.
"""

from core.tests.fixtures.api_fixtures import (  # noqa: F401
    api,
    api_client,
    django_client,
)
