"""
capturar_dni_inexistente.py — Captura qué HTML devuelve SUNAT cuando el DNI no existe.
"""

import random
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def token():
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(chars) for _ in range(52))


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-PE,es;q=0.9",
    })

    print("Init session...")
    session.get(f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp", timeout=(10, 120))

    # DNI que NO existe
    for dni in ("99999999", "87654321", "00000002"):
        print(f"\n{'='*70}\nDNI: {dni} (no existe)\n{'='*70}")
        data = {
            "accion": "consPorTipdoc",
            "razSoc": "",
            "nroRuc": "",
            "nrodoc": dni,
            "token": token(),
            "contexto": "ti-it",
            "modo": "1",
            "rbtnTipo": "2",
            "search1": "",
            "tipdoc": "1",
            "search2": dni,
            "search3": "",
            "codigo": "",
        }
        r = session.post(
            f"{BASE_URL}/jcrS00Alias",
            data=data,
            headers={"Referer": f"{BASE_URL}/FrameCriterioBusquedaWeb.jsp"},
            timeout=(10, 120),
        )
        soup = BeautifulSoup(r.text, "lxml")

        # Lo que el worker busca
        aRucs = soup.find_all("a", class_="aRucs")
        list_groups = soup.find_all("div", class_="list-group")
        title = soup.find("title")

        print(f"  status={r.status_code} bytes={len(r.text)}")
        print(f"  title={title.get_text(strip=True) if title else None!r}")
        print(f"  aRucs encontrados: {len(aRucs)}")
        print(f"  list-group divs encontrados: {len(list_groups)}")

        # Texto completo para buscar señales
        text = soup.get_text()
        text_lower = text.lower()
        for sig in ["no se encontr", "no existe", "no es válido", "no es valido", "no se puede", "error", "captcha"]:
            if sig in text_lower:
                print(f"  señal encontrada en texto: {sig!r}")

        # Mostrar primeros 800 chars de texto
        print(f"\n  --- TEXTO (primeros 600 chars) ---")
        print(text[:600])
        print(f"  --- FIN TEXTO ---")


if __name__ == "__main__":
    main()