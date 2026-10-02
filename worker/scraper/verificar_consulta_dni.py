"""
verificar_consulta_dni.py — Ejecuta la lógica del worker DIRECTAMENTE (sin servidor)
para DNI 74827847 y muestra paso a paso qué HTML recibe y qué decide el parser.

Corre con: uv run --no-project --with fastapi --with "pydantic>=2" --with requests
                --with beautifulsoup4 --with lxml python verificar_consulta_dni.py
"""

import json
import sys
from bs4 import BeautifulSoup

import documento_scraper
from documento_scraper import (
    consultar,
    TipoDocumento,
    _extract_ruc_from_dni_result,
    _extract_nombre_con_coma_desde_ruc_detail,
    _parse_dni,
    DocumentNotFoundError,
    ScraperFormatError,
)


def banner(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


def mostrar_html_resumido(html: str, label: str):
    soup = BeautifulSoup(html, "lxml")
    title = soup.find("title")
    aRucs = soup.find_all("a", class_="aRucs")
    list_groups = soup.find_all("div", class_="list-group")
    text = soup.get_text()

    print(f"\n  [{label}] status=200 bytes={len(html)}")
    print(f"  [{label}] title={title.get_text(strip=True) if title else None!r}")
    print(f"  [{label}] aRucs={len(aRucs)}  list-group={len(list_groups)}")
    print(f"\n  --- TEXTO (primeros 400 chars) ---")
    print(text[:400])
    print(f"  --- FIN ---")


def main():
    dni = sys.argv[1] if len(sys.argv) > 1 else "74827847"
    print(f"DNI a consultar: {dni}")

    banner("LLAMADA 1: consultar(dni) — el happy path completo")
    try:
        result = consultar(dni)
        print(f"\n  RESULTADO EXITOSO:")
        print(f"    tipo_documento={result.tipo_documento}")
        print(f"    numero_documento={result.numero_documento}")
        print(f"    razon_social={result.razon_social!r}")
    except DocumentNotFoundError as e:
        print(f"\n  DocumentNotFoundError: {e}")
    except ScraperFormatError as e:
        print(f"\n  ScraperFormatError: {e}")
        print(f"  parser_hint={e.parser_hint!r}")
        print(f"  retryable={e.retryable}")
    except Exception as e:
        print(f"\n  EXCEPCION INESPERADA: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()