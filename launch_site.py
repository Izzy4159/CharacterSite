import http.server
import socketserver
import webbrowser
import os
import contextlib
import threading
from time import monotonic, sleep
from urllib.parse import urlparse

CHARACTER_DIR = "characters"
PORT = 8000
IDLE_TIMEOUT_SECONDS = 20  # shutdown if no heartbeat within this window

# Heartbeat JS is injected into served HTML responses only (never written to disk)
HEARTBEAT_SNIPPET = """<script>
(function(){
  const ping = () => { try { fetch('/__ping__', {method:'POST', keepalive:true}); } catch(_){}
  };
  // initial ping + interval
  ping();
  setInterval(ping, 5000);
  // extra pings when the page is being hidden/navigated
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') ping();
  });
  window.addEventListener('pagehide', ping);
})();
</script>"""

THEME_CLASS = {
    "batman": "batman",
    "sasuke": "sasuke",
}

def project_root():
    return os.path.dirname(os.path.abspath(__file__))

def list_characters():
    try:
        files = os.listdir(CHARACTER_DIR)
        return sorted([os.path.splitext(f)[0] for f in files if f.endswith(".html")])
    except FileNotFoundError:
        return []

def ensure_index_exists():
    """Create a minimal index.html only if it doesn't exist. No scripts embedded."""
    path = os.path.join(project_root(), "index.html")
    if os.path.exists(path):
        return
    links = []
    for name in list_characters():
        cls = THEME_CLASS.get(name.lower(), "")
        links.append(f'<a href="{CHARACTER_DIR}/{name}.html" class="character-link {cls}">{name.capitalize()}</a>')
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Characters</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Anton&family=Roboto:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body class="index-page">
  <h1>Characters</h1>
  <div class="character-list">
    {' '.join(links) if links else '<p>No characters found.</p>'}
  </div>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

class ShutdownableHandler(http.server.SimpleHTTPRequestHandler):
    """Serves files, injects heartbeat into HTML, and accepts /__ping__ updates."""
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/__ping__":
            # update last ping timestamp
            try:
                self.server.last_ping = monotonic()
            except Exception:
                pass
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length:
                _ = self.rfile.read(length)
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        # Intercept HTML to inject heartbeat snippet automatically (response-only)
        path = self.translate_path(self.path)
        if os.path.isfile(path) and path.endswith(".html"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "</body>" in content:
                    content = content.replace("</body>", HEARTBEAT_SNIPPET + "\n</body>")
                else:
                    content = content + HEARTBEAT_SNIPPET
                data = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                # fall back to default behavior on any error
                pass
        # Non-HTML or fallback
        return super().do_GET()

    # Quiet logs
    def log_message(self, format, *args):
        pass

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def initiate_shutdown(self):
        with contextlib.suppress(Exception):
            self.shutdown()
            self.server_close()

def idle_monitor(server: "ThreadingTCPServer", timeout: int):
    """Background monitor to stop the server after no heartbeats for `timeout` seconds."""
    while True:
        sleep(2)
        now = monotonic()
        last = getattr(server, "last_ping", now)
        if (now - last) > timeout:
            print("⏳ No page heartbeat detected. Stopping server...")
            server.initiate_shutdown()
            break

def serve(port=PORT):
    os.chdir(project_root())
    httpd = ThreadingTCPServer(("", port), ShutdownableHandler)
    httpd.last_ping = monotonic()  # initialize heartbeat
    # start monitor thread
    threading.Thread(target=idle_monitor, args=(httpd, IDLE_TIMEOUT_SECONDS), daemon=True).start()
    return httpd

def main():
    # Only create an index if you don't already have one
    ensure_index_exists()

    print(f"🚀 Starting local server on http://localhost:{PORT}")
    httpd = serve(PORT)

    try:
        print("\n🧍 Available characters:")
        for name in list_characters():
            print(f" - {name}")

        url = f"http://localhost:{PORT}/index.html"
        print(f"\nOpening {url} in your browser...")
        webbrowser.open(url)

        print(f"\nℹ️ The server will stop automatically if the page is closed (idle > {IDLE_TIMEOUT_SECONDS}s).")
        httpd.serve_forever()
    finally:
        print("🛑 Server stopped.")
        with contextlib.suppress(Exception):
            httpd.server_close()

if __name__ == "__main__":
    main()
