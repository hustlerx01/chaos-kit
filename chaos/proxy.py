"""Minimal toxiproxy-style TCP fault injector (asyncio). Control via set_toxics().
Toxics: latency_ms (+ jitter_ms), drop_rate (close connection immediately), down (refuse all)."""
import asyncio, random, threading

class ChaosProxy:
    def __init__(self, listen_port: int, upstream: tuple[str, int]):
        self.listen_port, self.upstream = listen_port, upstream
        self.toxics = {"latency_ms": 0, "jitter_ms": 0, "drop_rate": 0.0, "down": False}
        self.loop = asyncio.new_event_loop(); self.server = None

    def set_toxics(self, **kw):
        self.toxics = {"latency_ms": 0, "jitter_ms": 0, "drop_rate": 0.0, "down": False, **kw}

    def _delay(self):
        t = self.toxics
        return max(0, t["latency_ms"] + random.uniform(-t["jitter_ms"], t["jitter_ms"])) / 1000

    async def _pipe(self, r, w, upstream_bound: bool):
        """Toxics are read per chunk, so faults also hit pooled keep-alive connections."""
        try:
            while data := await r.read(65536):
                if upstream_bound:
                    t = self.toxics
                    if t["down"] or random.random() < t["drop_rate"]:
                        break                      # reset mid-stream
                    d = self._delay()
                    if d: await asyncio.sleep(d)
                w.write(data); await w.drain()
        except (ConnectionError, asyncio.CancelledError): pass
        finally:
            try: w.close()
            except Exception: pass

    async def _handle(self, cr, cw):
        if self.toxics["down"]:
            cw.close(); return
        try:
            ur, uw = await asyncio.open_connection(*self.upstream)
        except OSError:
            cw.close(); return
        await asyncio.gather(self._pipe(cr, uw, True), self._pipe(ur, cw, False))

    def start(self):
        async def run():
            self.server = await asyncio.start_server(self._handle, "127.0.0.1", self.listen_port)
            async with self.server:
                try: await self.server.serve_forever()
                except asyncio.CancelledError: pass   # normal shutdown
        threading.Thread(target=lambda: self.loop.run_until_complete(run()), daemon=True).start()

    def stop(self):
        if self.server: self.loop.call_soon_threadsafe(self.server.close)
