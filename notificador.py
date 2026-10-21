import json
import os
import sys

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
ESTADO = os.path.join(BASE, "ultimo.json")

# Configura estos valores como variables de entorno o pégalos aquí.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def precio_actual():
    """COP por 1 USD. Prueba la TRM oficial y, si falla, una API gratuita."""
    try:
        r = requests.get(
            "https://www.datos.gov.co/resource/32sa-8pi3.json",
            params={"$order": "vigenciadesde DESC", "$limit": 1},
            timeout=20,
        )
        r.raise_for_status()
        return float(r.json()[0]["valor"]), "TRM oficial"
    except Exception as e:
        print("TRM falló:", e)
    r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=20)
    r.raise_for_status()
    return float(r.json()["rates"]["COP"]), "open.er-api.com"


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
    hoy, fuente = precio_actual()
    anterior = None
    if os.path.exists(ESTADO):
        with open(ESTADO) as f:
            anterior = json.load(f)["valor"]

    if anterior is not None and hoy < anterior:
        avisar(
            f"📉 El dólar bajó\n"
            f"Hoy: ${hoy:,.2f} COP\n"
            f"Antes: ${anterior:,.2f} COP\n"
            f"Diferencia: -${anterior - hoy:,.2f}\n"
            f"Fuente: {fuente}"
        )
    else:
        print(f"Sin baja. Hoy {hoy:,.2f} | antes {anterior} ({fuente})")

    with open(ESTADO, "w") as f:
        json.dump({"valor": hoy}, f)


if __name__ == "__main__":
    sys.exit(main())
