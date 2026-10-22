import json
import logging
import os
import sys

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(BASE, "ultimo.json")


def _cargar_env():
    ruta = os.path.join(BASE, ".env")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                clave, sep, valor = linea.strip().partition("=")
                if sep and not clave.startswith("#"):
                    os.environ.setdefault(clave.strip(), valor.strip())


_cargar_env()

# Variables de entorno, o el archivo .env junto a este script.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


UMBRAL = 10  # pesos de baja para avisar


def precio_actual():
    """COP por 1 USD (Yahoo Finance, intradia)."""
    r = requests.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/COP=X",
        params={"interval": "1m", "range": "1d"},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        },
        timeout=20,
    )
    r.raise_for_status()
    return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])


def avisar(texto):
    if not TOKEN or not CHAT_ID:
        print("[sin Telegram configurado]", texto)
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": texto},
        timeout=20,
    )
    r.raise_for_status()


def main():
    hoy = precio_actual()
    ref = hoy
    if os.path.exists(ESTADO):
        with open(ESTADO) as f:
            ref = json.load(f)["valor"]

    if ref - hoy >= UMBRAL:
        avisar(
            f"📉 El dólar bajó ${ref - hoy:,.2f}\n"
            f"Ahora: ${hoy:,.2f} COP\n"
            f"Referencia: ${ref:,.2f} COP"
        )
        ref = hoy
    else:
        ref = max(ref, hoy)  # la referencia sigue el maximo reciente
        logging.info(f"Sin aviso. Ahora {hoy:,.2f} | referencia {ref:,.2f}")

    with open(ESTADO, "w") as f:
        json.dump({"valor": ref}, f)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sys.exit(main())
