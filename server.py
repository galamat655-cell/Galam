import http.server
import os
import pathlib
import socketserver

PORT = int(os.environ.get("PORT", "10000"))
ROOT = pathlib.Path("/app/public")

class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.split("?", 1)[0].lstrip("/")
        if not rel:
            rel = "status.txt"
        return str(ROOT / rel)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/status.txt"):
            body = b"ready\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

print(f"Serving prebuilt mix on 0.0.0.0:{PORT}", flush=True)
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
