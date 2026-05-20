from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.services.database import get_galaxy_payload
from app.services.indexer import run_incremental_index


class NeuralNotesHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send(200, {"ok": True, "service": "neuralnotes-stdlib"})
        elif self.path == "/api/galaxy":
            self._send(200, get_galaxy_payload())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/sync":
            self._send(200, run_incremental_index())
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:
        print("[NeuralNotes]", format % args)


if __name__ == "__main__":
    run_incremental_index()
    server = ThreadingHTTPServer(("127.0.0.1", 8717), NeuralNotesHandler)
    print("NeuralNotes stdlib API running at http://127.0.0.1:8717")
    server.serve_forever()
