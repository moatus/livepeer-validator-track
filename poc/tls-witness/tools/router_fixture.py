"""Local TLS 1.2 router fixture, derived from the streaming router fixture.
Persistent synthetic credential from the environment; no key lifecycle routes.
Records accept/reject and request counts, never headers or credential values.
"""
import http.server, ssl, json, pathlib, time, threading, os, argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('record_dir', type=pathlib.Path)
parser.add_argument('port', type=int)
parser.add_argument('--response-bytes', type=int)
parser.add_argument('--credential-header', choices=['authorization','x-api-key'], default='authorization')
args = parser.parse_args()
if args.response_bytes is not None and not 0 <= args.response_bytes <= 32 * 1024 * 1024:
    parser.error('--response-bytes must be between 0 and 32 MiB')
R = args.record_dir; R.mkdir(parents=True, exist_ok=True)
C = pathlib.Path('target/tlsn-src/crates/server-fixture/certs/src/tls')
credential = os.environ['WITNESS_FIXTURE_CREDENTIAL']
lock = threading.Lock()
def log(event, **fields):
    with lock:
        with (R/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(event=event, unix_ns=time.time_ns(), **fields))+'\n')
class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    def get_request(self):
        sock, addr = self.socket.accept()
        log('connection')
        try: return ctx.wrap_socket(sock, server_side=True), addr
        except Exception: sock.close(); log('handshake_closed'); raise
class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        values = self.headers.get_all(args.credential_header, [])
        accepted = len(values) == 1 and values[0] == ('Bearer ' if args.credential_header == 'authorization' else '') + credential
        log('request', receipt_id=self.headers.get('X-Job-Id'), path=self.path, accepted=accepted, body_bytes=len(body))
        status = 200 if accepted else 401
        data = b'{"reply":"fixture pong"}' if accepted else b'{"error":"unauthorized"}'
        if accepted and args.response_bytes is not None:
            data = b'x' * args.response_bytes
        self.send_response(status); self.send_header('Content-Type', 'application/octet-stream' if accepted and args.response_bytes is not None else 'application/json')
        self.send_header('Content-Length', str(len(data))); self.send_header('Connection', 'close'); self.end_headers()
        self.wfile.write(data); self.close_connection = True
    def do_GET(self):
        log('unexpected_route', method='GET', path=self.path)
        self.send_error(404)
    def do_PATCH(self):
        log('unexpected_route', method='PATCH', path=self.path)
        self.send_error(404)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.maximum_version = ssl.TLSVersion.TLSv1_2
ctx.load_cert_chain(C/'test_server.crt', C/'test_server.key')
server = Server(('127.0.0.1', args.port), Handler)
print('fixture ready', flush=True); server.serve_forever()
