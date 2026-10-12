"""Upstream service.
RESILIENCE=0: 5s timeout, no retry, no fallback (naive)
RESILIENCE=1: 300ms timeout + 1 retry on ANY error + last-known-good cache fallback
RESILIENCE=2 (tuned after chaos run 1): 150ms timeout, retry ONLY on connect/reset errors (not timeouts), cache fallback"""
import os, time, httpx
from fastapi import FastAPI, Response
app = FastAPI()
INV = os.getenv("INVENTORY_URL", "http://127.0.0.1:7002")
LEVEL = os.getenv("RESILIENCE", "0")
RES = LEVEL in ("1", "2")
TIMEOUT = {"0": 5.0, "1": 0.3, "2": 0.15}[LEVEL]
CACHE: dict[str, dict] = {}
client = httpx.Client(timeout=TIMEOUT)

@app.get("/healthz")
def h(): return {"ok": True, "resilience": LEVEL}

@app.get("/product/{sku}")
def product(sku: str, resp: Response):
    attempts = 2 if RES else 1
    for i in range(attempts):
        try:
            r = client.get(f"{INV}/stock/{sku}"); r.raise_for_status()
            CACHE[sku] = r.json()
            return {"sku": sku, "in_stock": r.json()["qty"] > 0, "source": "live"}
        except (httpx.HTTPError, ValueError) as e:
            if LEVEL == "2" and isinstance(e, httpx.TimeoutException):
                break                      # a slow dependency won't get faster on retry; go to fallback
            if i + 1 < attempts: time.sleep(0.05)
    if RES and sku in CACHE:
        resp.headers["X-Degraded"] = "cache"
        return {"sku": sku, "in_stock": CACHE[sku]["qty"] > 0, "source": "cache"}
    resp.status_code = 503
    return {"error": "inventory unavailable"}
