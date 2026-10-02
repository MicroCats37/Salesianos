"""Strip `categoria_id=...` from test factory calls."""
import pathlib
import re

path = pathlib.Path(
    "modules/inscripciones/tests/integration/test_inscripciones_lifecycle.py"
)
src = path.read_text(encoding="utf-8")
new = re.sub(
    r'        categoria_id=str\(base_inscripcion_setup\["categoria"\]\.id\),\n',
    '',
    src,
)
path.write_text(new, encoding="utf-8")
print("ok")
