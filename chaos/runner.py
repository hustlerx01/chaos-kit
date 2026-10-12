"""Chaos experiment runner: steady-state -> inject -> measure -> rollback -> verify recovery."""
from __future__ import annotations
import argparse, json, os, signal, statistics, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx, yaml
from .proxy import ChaosProxy

PY = sys.executable
ROOT = Path(__file__).resolve().parents[1]
INV_PORT, PROXY_PORT, GW_PORT = 7002, 7012, 7001

def start(mod, port, env=None):
    return subprocess.Popen([PY, "-m", "uvicorn", f"services.{mod}:app", "--port", str(port), "--log-level", "warning"],
                            cwd=ROOT, env={**os.environ, **(env or {})})

def wait_up(url, t=15):
    end = time.time() + t
    while time.time() < end:
        try:
            if httpx.get(url, timeout=0.5).status_code == 200: return True
        except httpx.HTTPError: pass
        time.sleep(0.1)
    return False

def load(url, seconds, rps=40, workers=8):
    """Closed-ish loop load: returns per-request (latency_s, ok, degraded)."""
    res, end = [], time.time() + seconds
    def one():
        t0 = time.perf_counter()
        try:
            r = httpx.get(url, timeout=6)
            return time.perf_counter() - t0, r.status_code == 200, r.headers.get("X-Degraded") == "cache"
        except httpx.HTTPError:
            return time.perf_counter() - t0, False, False
    with ThreadPoolExecutor(workers) as ex:
        futs = []
        while time.time() < end:
            futs.append(ex.submit(one)); time.sleep(1 / rps)
        res = [f.result() for f in futs]
    return res

def summarize(res):
    lat = sorted(r[0] for r in res); n = len(res)
    return {"requests": n, "error_rate": round(1 - sum(r[1] for r in res) / n, 4),
            "degraded_rate": round(sum(r[2] for r in res) / n, 4),
            "p50_ms": round(statistics.median(lat) * 1000, 1), "p95_ms": round(lat[int(0.95 * (n - 1))] * 1000, 1),
            "max_ms": round(lat[-1] * 1000, 1)}

def check(h, s):
    return s["error_rate"] <= h["max_error_rate"] and s["p95_ms"] <= h["max_p95_ms"]

MODES = {"off": "0", "on": "1", "tuned": "2"}

def run_experiment(exp: dict, mode: str) -> dict:
    procs = {"inventory": start("inventory", INV_PORT)}
    proxy = ChaosProxy(PROXY_PORT, ("127.0.0.1", INV_PORT)); proxy.start()
    procs["gateway"] = start("gateway", GW_PORT, {"INVENTORY_URL": f"http://127.0.0.1:{PROXY_PORT}", "RESILIENCE": MODES[mode]})
    try:
        assert wait_up(f"http://127.0.0.1:{INV_PORT}/healthz") and wait_up(f"http://127.0.0.1:{GW_PORT}/healthz")
        url, h, d = f"http://127.0.0.1:{GW_PORT}/product/sku-1", exp["hypothesis"], exp.get("duration_s", 10)
        steady = summarize(load(url, d))
        f = exp["fault"]
        if f["type"] == "network":
            proxy.set_toxics(**f["toxics"])
        elif f["type"] == "kill":
            procs["inventory"].send_signal(signal.SIGKILL)
        t_fault = time.time()
        during = summarize(load(url, d))
        # rollback
        proxy.set_toxics()
        if f["type"] == "kill":
            time.sleep(f.get("restart_after_s", 0)); procs["inventory"] = start("inventory", INV_PORT)
            wait_up(f"http://127.0.0.1:{INV_PORT}/healthz")
        recovery = summarize(load(url, d))
        return {"experiment": exp["name"], "resilience": mode, "fault": f, "hypothesis": h,
                "steady": steady, "during": during, "recovery": recovery,
                "steady_ok": check(h, steady), "during_ok": check(h, during), "recovered": check(h, recovery)}
    finally:
        for p in procs.values():
            p.kill(); p.wait()
        proxy.stop(); time.sleep(0.2)

def to_markdown(results):
    rows = ["| Experiment | Resilience | Phase | req | err% | degraded% | p50 ms | p95 ms | hypothesis |", "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        for ph in ("steady", "during", "recovery"):
            s = r[ph]; ok = r[f"{ph}_ok" if ph != "recovery" else "recovered"]
            rows.append(f"| {r['experiment']} | {r['resilience']} | {ph} | {s['requests']} | {s['error_rate']*100:.1f} | {s['degraded_rate']*100:.1f} | {s['p50_ms']} | {s['p95_ms']} | {'PASS' if ok else 'FAIL'} |")
    return "\n".join(rows)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("experiments", nargs="+"); ap.add_argument("--out", default="results")
    ap.add_argument("--modes", default="off,on,tuned"); ap.add_argument("--duration", type=float)
    a = ap.parse_args(); results = []
    for path in a.experiments:
        exp = yaml.safe_load(open(path))
        if a.duration: exp["duration_s"] = a.duration
        for m in a.modes.split(","):
            r = run_experiment(exp, m); results.append(r)
            print(f"{r['experiment']:<22} resilience={m:<5} steady={r['steady_ok']} during={r['during_ok']} recovered={r['recovered']} "
                  f"(during err={r['during']['error_rate']:.2%} p95={r['during']['p95_ms']}ms)", flush=True)
    Path(a.out).mkdir(exist_ok=True)
    Path(a.out, "chaos_results.json").write_text(json.dumps(results, indent=1))
    Path(a.out, "chaos_report.md").write_text(to_markdown(results) + "\n")

if __name__ == "__main__":
    main()
