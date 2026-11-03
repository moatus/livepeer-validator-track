"""Local TLS sizing target. Synthetic authentication; never logs credentials."""
import argparse
import http.server
import json
import os
import pathlib
import ssl
import threading
import time

p = argparse.ArgumentParser()
p.add_argument('--port', type=int, required=True)
p.add_argument('--records', type=pathlib.Path, required=True)
p.add_argument('--cert-dir', type=pathlib.Path, required=True)
p.add_argument('--credential-header', choices=['authorization','x-api-key'], default='authorization')
a = p.parse_args()
a.records.mkdir(parents=True, exist_ok=True)
credential = os.environ['WITNESS_FIXTURE_CREDENTIAL']
lock = threading.Lock()

def log(**row):
    with lock, (a.records / 'events.jsonl').open('a') as f:
        f.write(json.dumps(dict(unix_ns=time.time_ns(), **row)) + '\n')

class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_):
        pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        values = self.headers.get_all(a.credential_header, [])
        accepted = len(values) == 1 and values[0] == ('Bearer ' if a.credential_header == 'authorization' else '') + credential
        try:
            cfg = json.loads(body)
            size = int(cfg.get('response_bytes', 1024))
            stream = cfg.get('stream', False)
            assert 0 <= size <= 10 * 1024**2
        except Exception:
            accepted, size, stream = False, 32, False
        log(event='request', receipt_id=self.headers.get('X-Job-Id'),
            body_bytes=len(body), response_bytes=size, stream=stream, accepted=accepted)
        self.send_response(200 if accepted else 401)
        self.send_header('Content-Type', 'text/event-stream' if stream else 'application/octet-stream')
        self.send_header('Connection', 'close')
        if stream:
            self.send_header('Transfer-Encoding', 'chunked')
        else:
            self.send_header('Content-Length', str(size))
        self.end_headers()
        if stream:
            # Exactly 64 KiB of SSE event bytes, in 32 chunks over 3 seconds.
            chunk = b'data: ' + b'x' * (2048 - 8) + b'\n\n'
            for _ in range(32):
                self.wfile.write(f'{len(chunk):x}\r\n'.encode() + chunk + b'\r\n')
                self.wfile.flush()
                time.sleep(3 / 32)
            self.wfile.write(b'0\r\n\r\n')
        else:
            chunk = b'x' * min(size, 65536)
            remaining = size
            while remaining:
                n = min(len(chunk), remaining)
                self.wfile.write(chunk[:n])
                remaining -= n
        self.close_connection = True
    def do_GET(self):
        log(event='unexpected_route', method='GET')
        self.send_error(404)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.maximum_version = ssl.TLSVersion.TLSv1_2
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ctx.load_cert_chain(a.cert_dir / 'test_server.crt', a.cert_dir / 'test_server.key')
s = Server(('127.0.0.1', a.port), Handler)
s.socket = ctx.wrap_socket(s.socket, server_side=True)
print('fixture ready', flush=True)
s.serve_forever()
