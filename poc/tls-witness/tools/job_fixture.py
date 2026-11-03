"""Local HTTPS submit/poll/fetch fixture. No credential values enter records."""
import http.server, ssl, json, pathlib, sys, time, threading, secrets, hashlib
R = pathlib.Path(sys.argv[1]); lock = threading.RLock(); credentials = {}; jobs = {}; serial = 0
C = pathlib.Path('target/tlsn-src/crates/server-fixture/certs/src/tls')
def log(event, **fields):
    with lock:
        with (R/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(event=event, unix_ns=time.time_ns(), **fields))+'\n')
class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    def get_request(self):
        sock, addr = self.socket.accept()
        try: return ctx.wrap_socket(sock, server_side=True), addr
        except Exception: sock.close(); raise
class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_): pass
    def body(self): return json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
    def reply(self, status, body, content_type='application/json'):
        if not isinstance(body, bytes): body = json.dumps(body, separators=(',', ':')).encode()
        self.send_response(status); self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body))); self.send_header('Connection','close'); self.end_headers()
        self.wfile.write(body); self.close_connection = True
    def authenticated(self):
        credential = self.headers.get('Authorization','').removeprefix('Bearer ')
        with lock:
            entry = credentials.get(credential)
            accepted = entry is not None and not entry['disabled']
            handle = entry['provider_hash'] if entry else None
        log('authentication', receipt_id=self.headers.get('X-Job-Id'), target=self.path, accepted=accepted, provider_hash=handle)
        return accepted
    def do_POST(self):
        global serial
        body = self.body()
        if self.path == '/keys':
            with lock:
                serial += 1; handle = 'fixture-hash-'+str(serial); credential = secrets.token_hex(32)
                credentials[credential] = dict(provider_hash=handle,disabled=False)
            log('obtain',provider_hash=handle)
            self.reply(201,dict(key=credential,data=dict(hash=handle,disabled=False,limit=body['limit'],include_byok_in_limit=True)))
        elif self.path == '/probe':
            self.reply(200 if self.authenticated() else 401, {})
        elif self.path == '/jobs':
            if not self.authenticated(): self.reply(401,{}); return
            with lock:
                job_id = secrets.token_hex(12)
                result = ('fixture result '+job_id+' '+body.get('input','')).encode()
                jobs[job_id] = dict(result=result,ready=time.monotonic()+(1.5 if body.get('fixture_mode')=='pending' else 0.4),mode=body.get('fixture_mode'))
            log('submit',receipt_id=self.headers.get('X-Job-Id'),job_id=job_id)
            self.reply(201,dict(job_id=job_id))
        else: self.reply(404,{})
    def do_GET(self):
        if self.path == '/state':
            with lock: value = dict(credentials=[dict(v) for v in credentials.values()], jobs=list(jobs))
            self.reply(200,value); return
        if self.path.startswith('/keys/'):
            handle = self.path[6:]
            with lock: entry = next((v for v in credentials.values() if v['provider_hash']==handle),None)
            self.reply(200,dict(data=dict(disabled=entry['disabled']))); return
        if not self.authenticated(): self.reply(401,{}); return
        parts = self.path.split('/')
        if len(parts)!=4 or parts[1]!='jobs' or parts[2] not in jobs: self.reply(404,{}); return
        job_id, action = parts[2:]; job = jobs[job_id]
        if action == 'poll':
            done = time.monotonic() >= job['ready']
            log('poll',receipt_id=self.headers.get('X-Job-Id'),job_id=job_id,state='done' if done else 'pending')
            self.reply(200,dict(state='done',digest=hashlib.sha256(job['result']).hexdigest()) if done else dict(state='pending'))
        elif action == 'result':
            log('fetch',receipt_id=self.headers.get('X-Job-Id'),job_id=job_id)
            self.reply(200,job['result']+(b' corrupted' if job['mode']=='bad-digest' else b''),'application/octet-stream')
        else: self.reply(404,{})
    def do_PATCH(self):
        self.body(); handle = self.path.removeprefix('/keys/')
        with lock:
            for entry in credentials.values():
                if entry['provider_hash']==handle: entry['disabled']=True
        log('disable',provider_hash=handle); self.reply(200,{})
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.maximum_version=ssl.TLSVersion.TLSv1_2
ctx.load_cert_chain(C/'test_server.crt',C/'test_server.key')
server = Server(('127.0.0.1',4017),Handler); print('fixture ready',flush=True); server.serve_forever()
