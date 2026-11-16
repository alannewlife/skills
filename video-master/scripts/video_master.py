#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import workflow
import credentials

ROOT = Path(__file__).resolve().parents[1]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        route = urlsplit(self.path).path
        if route == '/api/state': return self.send_json(200, workflow.read(self.server.project))
        if route == '/api/story':
            return self.send_json(200, {'story': (self.server.project / 'source/story.md').read_text(encoding='utf-8')})
        if route == '/api/health': return self.send_json(200, {'ok': True})
        if route == '/api/final-file':
            state = workflow.read(self.server.project)
            final = state.get('stages', {}).get('final', {})
            video = final.get('data', {}).get('video')
            available = state.get('active') == 'done' and final.get('status') == 'confirmed' and workflow.safe_file(self.server.project, video)
            return self.send_json(200, {'path': str((self.server.project / video).resolve()) if available else None})
        if route == '/api/agent': return self.send_json(200, workflow.waiter_status(self.server.project))
        if route == '/api/credentials':
            try: return self.send_json(200, credentials.status())
            except credentials.CredentialError as e: return self.send_json(503, {'error': str(e)})
        if route == '/': base, sub = ROOT / 'ui', 'index.html'
        elif route.startswith('/ui/'): base, sub = ROOT / 'ui', unquote(route[4:])
        elif route.startswith('/styles/'): base, sub = ROOT / 'styles', unquote(route[8:])
        elif route.startswith('/project/'): base, sub = self.server.project, unquote(route[9:])
        else: return self.send_error(404)
        base = base.resolve(); path = (base / sub).resolve()
        if not path.is_relative_to(base) or not path.is_file() or path.name.startswith('.'): return self.send_error(404)
        # Source and project JSON have dedicated limited APIs; don't expose unrelated project files.
        if route.startswith('/project/') and (not sub.startswith(('assets/', 'video/', 'output/', 'review/')) or path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp','.mp4','.webm','.wav','.mp3')): return self.send_error(404)
        size = path.stat().st_size; start, end = 0, size - 1
        byte_range = self.headers.get('Range')
        if byte_range:
            try:
                a, b = byte_range.removeprefix('bytes=').split('-', 1)
                if a: start = int(a); end = int(b) if b else end
                else: start = max(0, size - int(b))
                if start < 0 or end < start or start >= size: raise ValueError()
                end = min(end, size - 1)
            except ValueError: return self.send_error(416)
        self.send_response(206 if byte_range else 200)
        self.send_header('Content-Type', mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(end-start+1)); self.send_header('Accept-Ranges', 'bytes')
        self.send_header('X-Content-Type-Options', 'nosniff'); self.send_header('Cache-Control', 'no-store')
        if byte_range: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        with path.open('rb') as f:
            f.seek(start); remaining = end-start+1
            while remaining:
                chunk = f.read(min(65536, remaining))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): break
                remaining -= len(chunk)
    def do_POST(self):
        if self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}': return self.send_json(403, {'error':'请求来源不匹配'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 8*1024*1024: raise workflow.Invalid('请求大小无效')
            obj = json.loads(self.rfile.read(length))
            route = urlsplit(self.path).path
            if route == '/api/save': state = workflow.submit(self.server.project, obj['stage'], obj.get('data', {}), obj['revision'], False)
            elif route == '/api/confirm': state = workflow.submit(self.server.project, obj['stage'], obj.get('data', {}), obj['revision'], True)
            elif route == '/api/reopen': state = workflow.reopen(self.server.project, obj['stage'], obj['revision'])
            elif route == '/api/brand':
                content = base64.b64decode(obj['content'], validate=True) if obj.get('content') else None
                state = workflow.replace_brand(self.server.project, obj['revision'], obj.get('filename'), content)
            elif route == '/api/credentials':
                if obj.get('action') == 'save': credentials.save_key(obj.get('key'))
                elif obj.get('action') == 'delete': credentials.delete_key()
                else: raise workflow.Invalid('操作不支持')
                return self.send_json(200, credentials.status())
            else: return self.send_error(404)
            self.send_json(200, state)
        except workflow.Conflict as e: self.send_json(409, {'error': str(e)})
        except (workflow.Invalid, credentials.CredentialError, ValueError, KeyError, TypeError) as e: self.send_json(400, {'error': str(e)})

class Server(ThreadingHTTPServer):
    daemon_threads = True

def main():
    parser = argparse.ArgumentParser(description='Video Master 本地项目与确认页面')
    sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('project'); p.add_argument('--story', required=True); p.add_argument('--logo')
    p = sub.add_parser('status'); p.add_argument('project')
    p = sub.add_parser('upgrade'); p.add_argument('project'); p.add_argument('--expected-revision', type=int, required=True)
    p = sub.add_parser('propose'); p.add_argument('project'); p.add_argument('stage', choices=workflow.STAGES); p.add_argument('--json', required=True, help='提案 JSON 文件'); p.add_argument('--expected-revision', type=int, default=None)
    p = sub.add_parser('serve'); p.add_argument('project'); p.add_argument('--port', type=int, default=0); p.add_argument('--no-browser', action='store_true')
    p = sub.add_parser('wait'); p.add_argument('project'); p.add_argument('stage', choices=workflow.STAGES); p.add_argument('--timeout', type=int, default=50); p.add_argument('--after-revision', type=int, default=None)
    args = parser.parse_args(); project = Path(args.project).resolve()
    try:
        if args.cmd == 'init': print(json.dumps(workflow.initialize(project, args.story, args.logo), ensure_ascii=False, indent=2))
        elif args.cmd == 'status': print(json.dumps(workflow.read(project), ensure_ascii=False, indent=2))
        elif args.cmd == 'upgrade': print(json.dumps(workflow.upgrade(project, args.expected_revision), ensure_ascii=False, indent=2))
        elif args.cmd == 'propose': print(json.dumps(workflow.propose(project, args.stage, json.loads(Path(args.json).read_text(encoding='utf-8')), expected_revision=args.expected_revision), ensure_ascii=False, indent=2))
        elif args.cmd == 'wait':
            deadline = time.monotonic() + min(max(args.timeout, 0), 50)
            with workflow.waiter(project, args.stage) as pulse:
                while True:
                    state = workflow.read(project)
                    if state['stages'][args.stage]['status'] == 'confirmed' or (args.after_revision is not None and state['revision'] > args.after_revision):
                        print(json.dumps(state, ensure_ascii=False)); break
                    if time.monotonic() >= deadline: print('等待中：尚未确认。可再次等待或在用户回复后恢复。', file=sys.stderr); return 2
                    pulse()
                    time.sleep(.4)
        elif args.cmd == 'serve':
            workflow.read(project)
            server = Server(('127.0.0.1', args.port), Handler); server.project = project
            url = f'http://127.0.0.1:{server.server_port}/'
            print(f'Video Master: {url}\n项目: {project}', flush=True)
            if not args.no_browser: webbrowser.open(url)
            try: server.serve_forever()
            except KeyboardInterrupt: pass
            finally: server.server_close()
    except (workflow.Invalid, workflow.Conflict, OSError, ValueError) as e:
        print(f'错误：{e}', file=sys.stderr); return 1
    return 0
if __name__ == '__main__': sys.exit(main())
