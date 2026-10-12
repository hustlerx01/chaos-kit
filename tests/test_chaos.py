import socket, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx, pytest
from chaos.proxy import ChaosProxy
from chaos.runner import summarize, check

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

@pytest.fixture
def proxy():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    px = ChaosProxy(free_port(), ("127.0.0.1", srv.server_address[1])); px.start(); time.sleep(0.2)
    yield px; px.stop(); srv.shutdown()

def test_passthrough(proxy):
    assert httpx.get(f"http://127.0.0.1:{proxy.listen_port}/").text == "ok"

def test_latency_applies_to_pooled_connection(proxy):
    with httpx.Client() as c:
        url = f"http://127.0.0.1:{proxy.listen_port}/"
        c.get(url)                                   # connection now pooled
        proxy.set_toxics(latency_ms=300)
        t0 = time.perf_counter(); c.get(url); assert time.perf_counter() - t0 >= 0.28

def test_down_refuses(proxy):
    proxy.set_toxics(down=True)
    with pytest.raises(httpx.HTTPError):
        httpx.get(f"http://127.0.0.1:{proxy.listen_port}/", timeout=1)

def test_summary_and_hypothesis():
    s = summarize([(0.01, True, False)] * 90 + [(1.0, False, False)] * 10)
    assert s["error_rate"] == 0.1 and s["p95_ms"] == 1000.0
    assert not check({"max_error_rate": 0.01, "max_p95_ms": 400}, s)
