import os, json, urllib.request, urllib.parse

URLS = os.environ["PRODUCT_URL"].split()
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]
STATE = "state.json"

state = json.load(open(STATE)) if os.path.exists(STATE) else {}

for url in URLS:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print(url, "fetch error:", e)
        continue

    if ("captcha" in html.lower() or "api-services-support@amazon.com" in html
            or "Click the button below to continue shopping" in html):
        status = "blocked"
    elif 'id="add-to-cart-button"' in html or 'id="buy-now-button"' in html:
        status = "available"
    else:
        status = "unavailable"

    prev = state.get(url, "")
    print(f"{url} prev={prev or '-'} now={status}")

    if status == "available" and prev != "available":
        data = urllib.parse.urlencode({"chat_id": CHAT, "text": f"¡Disponible en Amazon!\n{url}"}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data, timeout=30)

    # "blocked" no pisa el último estado conocido
    if status != "blocked":
        state[url] = status

json.dump(state, open(STATE, "w"))
