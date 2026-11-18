"""
test_worker_live.py — Ejecuta el worker REAL (uvicorn en :8765) y consulta DNIs
varios seguidos para ver si a partir de cierto request SUNAT empieza a devolver
HTML anti-bot y el worker muere con FORMAT_ERROR.

NO toca el código del worker. Solo hace requests HTTP al endpoint.
"""

import time
import json
import sys
import httpx


WORKER_URL = "http://127.0.0.1:8765"
DNIs = ["74827847", "45406196", "12345678", "99999999", "87654321", "45406196"]


def banner(t):
    print()
    print("=" * 70)
    print(t)
    print("=" * 70)


def main():
    print(f"Probando worker en {WORKER_URL}")
    print(f"DNIs a consultar (en orden): {DNIs}")

    with httpx.Client(timeout=180.0) as client:
        for i, dni in enumerate(DNIs, 1):
            banner(f"REQUEST {i}/{len(DNIs)} — DNI {dni}")
            t0 = time.time()
            try:
                r = client.get(f"{WORKER_URL}/consultar/{dni}")
                elapsed = time.time() - t0
                print(f"  status={r.status_code} tiempo={elapsed:.2f}s")
                print(f"  body={json.dumps(r.json(), indent=2, ensure_ascii=False)}")
            except Exception as e:
                elapsed = time.time() - t0
                print(f"  EXCEPCION tiempo={elapsed:.2f}s: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()