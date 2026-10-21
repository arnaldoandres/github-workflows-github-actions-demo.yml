import json
import os
import sys

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(BASE, "ultimo.json")

# Configura estos valores como variables de entorno o pégalos aquí.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


UMBRAL = 10  # pesos de baja para avisar


def precio_actual():
    """COP por 1 USD (Yahoo Finance, intradia)."""
    r = requests.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/COP=X",
        params={"interval": "1m", "range": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
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
        print(f"Sin aviso. Ahora {hoy:,.2f} | referencia {ref:,.2f}")

    with open(ESTADO, "w") as f:
        json.dump({"valor": ref}, f)


if __name__ == "__main__":
    sys.exit(main())
