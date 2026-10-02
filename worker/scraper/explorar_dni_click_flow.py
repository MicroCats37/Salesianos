"""
explorar_dni_click_flow.py
===========================

Script de exploración — NO toca documento_scraper.py.

Replica el flujo DNI → "click" en el primer RUC y muestra:
  1) El HTML de búsqueda por DNI (lo que ya tenés hoy)
  2) El data-ruc extraído del primer <a class="aRucs">
  3) El HTML del detalle de RUC al hacer la 2da POST (el "click")
  4) Todos los campos label/value que aparecen en el detalle
  5) Cualquier formato que tenga el nombre del representante legal

Uso:
    uv run python explorar_dni_click_flow.py [DNI]

Por defecto usa DNI=74827847 (CALLIRGOS OROZCO PIERO ALDAIR).
"""

import sys
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _generate_token(length: int = 52) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(chars) for _ in range(length))


def banner(titulo: str) -> None:
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


SEPARATOR = " -> "


def main():
    dni = sys.argv[1] if len(sys.argv) > 1 else "74827847"
    print(f"DNI objetivo: {dni}")

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9",
    })

    # ──────────────────────────────────────
    # Paso 0: init session (igual que el worker real)
    # ──────────────────────────────────────
    banner("PASO 0 — GET /FrameCriterioBusquedaWeb.jsp (init session)")
    r0 = session.get(
        f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp",
        timeout=(10, 120),
    )
    print(f"status={r0.status_code} bytes={len(r0.text)}")

    # ──────────────────────────────────────
    # Paso 1: búsqueda por DNI
    # ──────────────────────────────────────
    banner("PASO 1 — POST jcrS00Alias accion=consPorTipdoc (búsqueda DNI)")
    data_dni = {
        "accion": "consPorTipdoc",
        "razSoc": "",
        "nroRuc": "",
        "nrodoc": dni,
        "token": _generate_token(),
        "contexto": "ti-it",
        "modo": "1",
        "rbtnTipo": "2",
        "search1": "",
        "tipdoc": "1",
        "search2": dni,
        "search3": "",
        "codigo": "",
    }
    r1 = session.post(
        f"{BASE_URL}/jcrS00Alias",
        data=data_dni,
        headers={"Referer": f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp"},
        timeout=(10, 120),
    )
    r1.raise_for_status()
    soup1 = BeautifulSoup(r1.text, "lxml")
    print(f"status={r1.status_code} bytes={len(r1.text)}")

    # Mostrar todos los <a class="aRucs"> encontrados
    anchors = soup1.find_all("a", class_="aRucs")
    print(f"\naRucs encontrados: {len(anchors)}")
    for i, a in enumerate(anchors):
        h4s = [h.get_text(" ", strip=True) for h in a.find_all("h4")]
        ps = [p.get_text(" ", strip=True) for p in a.find_all("p")]
        print(f"\n  [{i}] data-ruc={a.get('data-ruc')!r}")
        for h in h4s:
            print(f"      h4: {h!r}")
        for p in ps:
            print(f"      p : {p!r}")

    if not anchors:
        print("\n⚠ No hay resultados para ese DNI. Fin.")
        return

    first = anchors[0]
    ruc = first.get("data-ruc")
    print(f"\n>>> Primer resultado — data-ruc={ruc!r}")

    # Guardar HTML completo del paso 1
    out1 = Path("/tmp/sunat_paso1_dni_search.html")
    out1.write_text(r1.text, encoding="utf-8")
    print(f"HTML paso 1 guardado en: {out1}")

    # ──────────────────────────────────────
    # Paso 2: "click" → POST consPorRuc con el RUC extraído
    # ──────────────────────────────────────
    banner(f"PASO 2 — POST jcrS00Alias accion=consPorRuc nroRuc={ruc!r} (el 'click')")
    data_ruc = {
        "accion": "consPorRuc",
        "razSoc": "",
        "nroRuc": ruc,
        "nrodoc": "",
        "token": _generate_token(),
        "contexto": "ti-it",
        "modo": "1",
        "rbtnTipo": "1",
        "search1": ruc,
        "tipdoc": "",
        "search2": "",
        "search3": "",
        "codigo": "",
    }
    r2 = session.post(
        f"{BASE_URL}/jcrS00Alias",
        data=data_ruc,
        headers={"Referer": f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp"},
        timeout=(10, 120),
    )
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, "lxml")
    print(f"status={r2.status_code} bytes={len(r2.text)}")

    # Guardar HTML completo del paso 2
    out2 = Path("/tmp/sunat_paso2_ruc_detail.html")
    out2.write_text(r2.text, encoding="utf-8")
    print(f"HTML paso 2 guardado en: {out2}")

    # ──────────────────────────────────────
    # Paso 3: dump de TODOS los label/value del detalle
    # ──────────────────────────────────────
    banner("PASO 3 — Todos los campos label/value del detalle de RUC")
    print("(Estructura: list-group-item > row > col-sm-X label | col-sm-Y value)\n")

    items = soup2.find_all("div", class_="list-group-item")
    campos: list[tuple[str, str]] = []
    for item in items:
        cols = item.find_all("div", class_=lambda c: c and "col-sm" in c)
        if len(cols) >= 2:
            label = " ".join(cols[0].get_text(" ", strip=True).split()).rstrip(":")
            value = " ".join(cols[1].get_text(" ", strip=True).split())
            campos.append((label, value))

    if not campos:
        print("⚠ No se encontraron list-group-item con pares label/value")
    else:
        for label, value in campos:
            print(f"  {label:35s}{SEPARATOR}{value!r}")

    # ──────────────────────────────────────
    # Paso 4: foco en el nombre del representante
    # ──────────────────────────────────────
    banner("PASO 4 — Búsqueda específica del NOMBRE del representante legal")
    print("Buscando cualquier campo que contenga 'CALLIRGOS':\n")

    page_text = soup2.get_text()
    if "CALLIRGOS" in page_text:
        print("[OK] 'CALLIRGOS' SI esta en el HTML del detalle")
    else:
        print("[NO] 'CALLIRGOS' NO esta en el HTML del detalle")

    # Detectar si aparece alguna coma en valores relevantes
    print("\nCampos con coma en el value:")
    for label, value in campos:
        if "," in value:
            print(f"  {label:35s}{SEPARATOR}{value!r}")

    print("\nCampos de 'nombre' / 'apellido':")
    for label, value in campos:
        low = label.lower()
        if "nombre" in low or "apellido" in low or "rep" in low:
            print(f"  {label:35s}{SEPARATOR}{value!r}")

    # ──────────────────────────────────────
    # Paso 5: dump de todos los <h4> del detalle
    # ──────────────────────────────────────
    banner("PASO 5 — Todos los <h4> del detalle")
    for h4 in soup2.find_all("h4"):
        text = h4.get_text(" ", strip=True)
        if text:
            print(f"  {text!r}")

    print("\n✓ Exploración completa.")


if __name__ == "__main__":
    main()