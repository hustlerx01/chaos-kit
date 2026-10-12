"""Downstream service: stock lookup."""
from fastapi import FastAPI
app = FastAPI()
STOCK = {"sku-1": 12, "sku-2": 0, "sku-3": 7}
@app.get("/healthz")
def h(): return {"ok": True}
@app.get("/stock/{sku}")
def stock(sku: str): return {"sku": sku, "qty": STOCK.get(sku, 0)}
