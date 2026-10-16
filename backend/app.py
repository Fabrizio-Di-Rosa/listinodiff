"""ListinoDiff feedback API. Python standard library only."""
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

DB_PATH = Path(os.environ.get("LISTINODIFF_DB", "/data/feedback.sqlite3"))
HOST = os.environ.get("LISTINODIFF_HOST", "0.0.0.0")
PORT = int(os.environ.get("LISTINODIFF_PORT", "8000"))
ALLOWED_ORIGIN = os.environ.get("LISTINODIFF_ORIGIN", "https://listinodiff.antefide.it")
RATE_LOCK = Lock()
RECENT = {}
FIELDS = {
    "settore": {"commercio", "servizi", "produzione", "altro"},
    "frequenza": {"giornaliera", "settimanale", "mensile", "occasionale"},
    "utilita": {"molto", "abbastanza", "poco", "per_niente"},
    "prezzo": {"si", "forse", "no"},
}
EMAIL_RE = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,190}$")

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        settore TEXT NOT NULL,
        frequenza TEXT NOT NULL,
        utilita TEXT NOT NULL,
        prezzo TEXT NOT NULL,
        email TEXT,
        ricontatto INTEGER NOT NULL CHECK(ricontatto IN (0,1))
    )""")
    conn.commit()
    return conn

def purge(conn):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    conn.execute("DELETE FROM feedback WHERE created_at < ?", (cutoff,))
    conn.commit()

def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Dati non validi")
    for field, allowed in FIELDS.items():
        if data.get(field) not in allowed:
            raise ValueError("Risposta non valida: " + field)
    email = data.get("email", "")
    consent = data.get("ricontatto") is True
    if not isinstance(email, str) or len(email) > 254:
        raise ValueError("Email non valida")
    email = email.strip()
    if email and (not consent or not EMAIL_RE.fullmatch(email)):
        raise ValueError("Email o consenso non validi")
    if consent and not email:
        raise ValueError("Inserisci un'email per il ricontatto")
    if data.get("website", ""):
        raise ValueError("Invio non valido")
    return tuple(data[k] for k in FIELDS) + (email or None, int(consent))

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self.respond(200, {"status": "ok"})
        else:
            self.respond(404, {"error": "Non trovato"})

    def do_POST(self):
        if self.path != "/feedback":
            return self.respond(404, {"error": "Non trovato"})
        if self.headers.get("Origin") != ALLOWED_ORIGIN:
            return self.respond(403, {"error": "Origine non autorizzata"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self.respond(415, {"error": "Formato non supportato"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400, {"error": "Dimensione non valida"})
        if not 0 < size <= 4096:
            return self.respond(413, {"error": "Richiesta troppo grande"})
        try:
            data = json.loads(self.rfile.read(size))
            values = validate(data)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)[:150]})
        # Conservative per-IP limit; Caddy should also rate-limit at edge if available.
        ip = self.client_address[0]
        now = time.monotonic()
        with RATE_LOCK:
            for key in list(RECENT):
                RECENT[key] = [t for t in RECENT[key] if now - t < 3600]
                if not RECENT[key]:
                    del RECENT[key]
            hits = RECENT.setdefault(ip, [])
            if len(hits) >= 5:
                return self.respond(429, {"error": "Troppi invii. Riprova più tardi."})
            hits.append(now)
        try:
            with connect() as conn:
                purge(conn)
                conn.execute(
                    """INSERT INTO feedback
                    (created_at, settore, frequenza, utilita, prezzo, email, ricontatto)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (datetime.now(timezone.utc).isoformat(), *values),
                )
                conn.commit()
        except sqlite3.Error:
            return self.respond(503, {"error": "Servizio temporaneamente non disponibile"})
        self.respond(201, {"status": "received"})

if __name__ == "__main__":
    with connect() as conn:
        purge(conn)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
