import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


PORT = int(os.getenv("MODEL_SERVICE_PORT", "8001"))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/health", "/healthz"):
            self._send_json(200, {"status": "ok", "service": "model_service"})
            return
        self._send_json(200, {"message": "model_service starter is running"})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"model_service listening on :{PORT}")
    server.serve_forever()
