import os, json, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright

URLS = os.environ["PRODUCT_URL"].split()
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ["TELEGRAM_CHAT_ID"]
STATE = "state.json"

state = json.load(open(STATE)) if os.path.exists(STATE) else {}

pw = sync_playwright().start()
browser = pw.chromium.launch()
ctx = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    locale="en-US",
)
page = ctx.new_page()


def fetch(url):
    page.goto(url, timeout=45000)
    btn = page.get_by_role("button", name="Continue shopping")
    if btn.count():
        btn.first.click()
        page.wait_for_load_state()
        page.wait_for_timeout(2000)
        page.goto(url, timeout=45000)
    return page.content()


for url in URLS:
    try:
        html = fetch(url)
    except Exception as e:
        print(url, "fetch error:", e)
        continue

    print(url, "title:", page.title(), "| len:", len(html))
    if ("Enter the characters you see below" in html
            or "Type the characters you see in this image" in html
            or "api-services-support@amazon.com" in html
            or "Click the button below to continue shopping" in html):
        status = "blocked"
    elif 'id="add-to-cart-button"' in html or 'id="buy-now-button"' in html:
        status = "available"
    elif 'id="productTitle"' not in html:
        status = "blocked"  # no es la página del producto
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

browser.close()
pw.stop()
json.dump(state, open(STATE, "w"))
