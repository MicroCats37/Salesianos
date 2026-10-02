"""Remove `evento_id=...` kwargs from test calls."""
import pathlib
import re

path = pathlib.Path("modules/inscripciones/tests/integration/test_inscripciones_lifecycle.py")
src = path.read_text(encoding="utf-8")
new = re.sub(
    r'        evento_id=str\(base_inscripcion_setup\["evento"\]\.id\),\n',
    '',
    src,
)
path.write_text(new, encoding="utf-8")
print("ok")
