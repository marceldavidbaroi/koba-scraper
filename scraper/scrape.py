import os, json
import requests
from bs4 import BeautifulSoup

BASE = "https://www.kobareseller.com"
LOGIN_PAGE = f"{BASE}/login"
LOGIN_POST = f"{BASE}/login"  # may differ; adjust if needed
TARGET_PAGE = f"{BASE}/dashboard/products?page=1&product=cosrx"
OUTFILE = "site/data.json"

def get_csrf(html: str):
    soup = BeautifulSoup(html, "lxml")
    el = soup.select_one('input[name="_token"]')
    return el["value"] if el else None

def main():
    email = os.environ.get("KOBA_EMAIL")
    password = os.environ.get("KOBA_PASSWORD")
    if not email or not password:
        raise SystemExit("Missing KOBA_EMAIL or KOBA_PASSWORD")

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    # 1) Get login page for cookies + CSRF token
    r = s.get(LOGIN_PAGE, timeout=30)
    r.raise_for_status()
    csrf = get_csrf(r.text)

    # 2) Login
    payload = {"email": email, "password": password}
    if csrf:
        payload["_token"] = csrf

    r = s.post(LOGIN_POST, data=payload, allow_redirects=True, timeout=30)
    r.raise_for_status()

    # 3) Fetch target page
    r = s.get(TARGET_PAGE, timeout=30)
    r.raise_for_status()

    # 4) Parse HTML (you will likely need to change selectors)
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    for row in soup.select("table tbody tr"):
        cols = [td.get_text(" ", strip=True) for td in row.select("td")]
        if cols:
            items.append({"cols": cols})

    data = {"source": TARGET_PAGE, "count": len(items), "items": items}
    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(items)} items to {OUTFILE}")

if __name__ == "__main__":
    main()
