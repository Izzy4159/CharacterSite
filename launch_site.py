import http.server
import socketserver
import webbrowser
import os
import json
import base64
import re
import html as html_mod
import contextlib
import threading
from time import monotonic, sleep
from urllib.parse import urlparse

CHARACTER_DIR = "characters"
PORT = 8000
IDLE_TIMEOUT_SECONDS = 20

HEARTBEAT_SNIPPET = """<script>
(function(){
  const ping = () => { try { fetch('/__ping__', {method:'POST', keepalive:true}); } catch(_){} };
  ping();
  setInterval(ping, 5000);
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

# Exact template shared by all character pages (slug is derived from filename by character.js)
CHARACTER_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Loading\u2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../character.css">
</head>
<body class="char-body">

  <nav class="char-nav" aria-label="Character navigation">
    <a href="../index.html" class="char-back">\u2039 Characters</a>
    <span class="edit-badge" id="edit-badge">Editing</span>
  </nav>

  <section class="char-hero">
    <p class="char-eyebrow" id="char-eyebrow"></p>
    <h1 class="char-title"  id="char-title"></h1>
    <p class="char-tagline" id="char-tagline"></p>
  </section>

  <section class="gallery-section" aria-label="Photo gallery">
    <div class="gallery-grid" id="gallery-grid"></div>
    <div class="add-photo-wrap" id="add-photo-wrap">
      <label class="add-photo-btn" for="photo-input">+ Add Photo</label>
      <input type="file" id="photo-input" accept="image/*" multiple>
    </div>
  </section>

  <section class="info-section" aria-label="Character info">
    <div class="info-inner">
      <div class="stats-grid" id="stats-grid"></div>
      <div class="bio-wrap"   id="bio-wrap"></div>
    </div>
  </section>

  <div class="fab-group" aria-label="Page actions">
    <button class="fab fab-save" id="fab-save" onclick="saveData()">Save Changes</button>
    <button class="fab fab-edit" id="fab-edit" onclick="toggleEdit()"
            aria-label="Toggle edit mode">
      <span class="fab-icon" aria-hidden="true">\u270f</span>
    </button>
  </div>

  <script src="../character.js"></script>
</body>
</html>
"""

def project_root():
    return os.path.dirname(os.path.abspath(__file__))

def list_characters():
    try:
        files = os.listdir(CHARACTER_DIR)
        return sorted([os.path.splitext(f)[0] for f in files if f.endswith(".html")])
    except FileNotFoundError:
        return []

def ensure_index_exists():
    path = os.path.join(project_root(), "index.html")
    if os.path.exists(path):
        return
    links = []
    for name in list_characters():
        cls = THEME_CLASS.get(name.lower(), "")
        links.append(f'<a href="{CHARACTER_DIR}/{name}.html" class="character-link {cls}">{name.capitalize()}</a>')
    html_content = f"""<!DOCTYPE html>
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
        f.write(html_content)


def _h(s):
    """HTML-escape a string for safe insertion into HTML attributes/text."""
    return html_mod.escape(str(s or ""), quote=True)


class ShutdownableHandler(http.server.SimpleHTTPRequestHandler):

    # ── POST routing ─────────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/__ping__":
            try:
                self.server.last_ping = monotonic()
            except Exception:
                pass
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length:
                self.rfile.read(length)
            self.send_response(204)
            self.end_headers()

        elif path == "/__save__":
            self._handle_save()

        elif path == "/__upload__":
            self._handle_upload()

        elif path == "/__new_character__":
            self._handle_new_character()

        else:
            self.send_error(404, "Not found")

    # ── Save character JSON ──────────────────────────────────────────
    def _handle_save(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))

            character = data.get("character", "").lower().strip()
            if not character or not re.match(r'^[a-z0-9_-]+$', character):
                self._json_error(400, "Invalid character name")
                return

            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", f"{character}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._json_ok({"success": True})
        except Exception as e:
            self._json_error(500, str(e))

    # ── Upload a photo ───────────────────────────────────────────────
    def _handle_upload(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))

            character = data.get("character", "").lower().strip()
            filename  = data.get("filename", "photo.jpg").strip()
            b64data   = data.get("data", "")

            if not character or not re.match(r'^[a-z0-9_-]+$', character):
                self._json_error(400, "Invalid character name")
                return

            filename = re.sub(r'[^\w\-.]', '_', filename) or "photo.jpg"
            if "," in b64data:
                b64data = b64data.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64data + "==")

            img_dir = os.path.join("images", character)
            os.makedirs(img_dir, exist_ok=True)

            base_name, ext = os.path.splitext(filename)
            out_path = os.path.join(img_dir, filename)
            counter = 1
            while os.path.exists(out_path):
                out_path = os.path.join(img_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            with open(out_path, "wb") as f:
                f.write(raw_bytes)

            url = "/images/{}/{}".format(character, os.path.basename(out_path))
            self._json_ok({"success": True, "url": url})
        except Exception as e:
            self._json_error(500, str(e))

    # ── Create a new character ───────────────────────────────────────
    def _handle_new_character(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))

            title = (data.get("title") or "").strip()
            if not title:
                self._json_error(400, "Character name is required")
                return

            # Derive URL-safe slug from title
            slug = re.sub(r'[^a-z0-9]', '', title.lower())
            if not slug:
                self._json_error(400, "Title must contain at least one letter or digit")
                return

            html_path = os.path.join(CHARACTER_DIR, f"{slug}.html")
            json_path = os.path.join("data", f"{slug}.json")
            if os.path.exists(html_path) or os.path.exists(json_path):
                self._json_error(409, f"A character with the slug '{slug}' already exists")
                return

            # Save background image if provided
            bg_url = ""
            bg_data = data.get("bgImage", "")
            bg_filename = re.sub(r'[^\w\-.]', '_', data.get("bgImageFilename", "bg.jpg") or "bg.jpg") or "bg.jpg"
            if bg_data:
                if "," in bg_data:
                    bg_data = bg_data.split(",", 1)[1]
                raw_bytes = base64.b64decode(bg_data + "==")
                img_dir = os.path.join("images", slug)
                os.makedirs(img_dir, exist_ok=True)
                out_path = os.path.join(img_dir, bg_filename)
                counter = 1
                base_n, ext_n = os.path.splitext(bg_filename)
                while os.path.exists(out_path):
                    out_path = os.path.join(img_dir, f"{base_n}_{counter}{ext_n}")
                    counter += 1
                with open(out_path, "wb") as f:
                    f.write(raw_bytes)
                bg_url = f"/images/{slug}/{os.path.basename(out_path)}"

            # Build theme from accent color
            accent     = data.get("accent") or "#3b82f6"
            accent_text = self._contrast_text(accent)
            accent_glow = self._hex_to_rgba(accent, 0.10)

            char_json = {
                "character": slug,
                "title":     title,
                "eyebrow":   (data.get("eyebrow") or "").strip(),
                "tagline":   (data.get("tagline") or "").strip(),
                "bgImage":   bg_url,
                "stats":     data.get("stats") or [],
                "bio":       data.get("bio") or [],
                "images":    ([{"src": bg_url, "alt": title}] if bg_url else []),
                "theme": {
                    "accent":     accent,
                    "accentText": accent_text,
                    "accentGlow": accent_glow,
                    "bg":         "#111111",
                    "surface":    "rgba(255,255,255,0.05)",
                    "border":     "rgba(255,255,255,0.09)",
                    "text":       "#ffffff",
                    "textMuted":  "rgba(255,255,255,0.55)",
                },
            }

            # Persist JSON
            os.makedirs("data", exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(char_json, f, indent=2, ensure_ascii=False)

            # Persist character HTML page
            os.makedirs(CHARACTER_DIR, exist_ok=True)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(CHARACTER_PAGE_TEMPLATE)

            # Patch index.html so the new section persists on refresh
            self._patch_index_html(char_json, bg_url)

            self._json_ok({
                "success":   True,
                "slug":      slug,
                "bgUrl":     bg_url,
                "character": char_json,
            })

        except Exception as e:
            self._json_error(500, str(e))

    # ── Patch index.html: inject style + section + dropdown entry ────
    def _patch_index_html(self, char, bg_url):
        index_path = "index.html"
        if not os.path.exists(index_path):
            return

        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        style_block  = self._build_section_style(char)
        section_html = self._build_section_html(char, bg_url)
        dropdown_html = self._build_dropdown_entry(char, bg_url)

        # Insert theme <style> before </head>
        if "</head>" in content:
            content = content.replace("</head>", style_block + "\n</head>", 1)

        # Insert section before sentinel (or fallback: before </main>)
        sentinel_sec = "<!-- [[CHAR_SECTIONS_END]] -->"
        if sentinel_sec in content:
            content = content.replace(sentinel_sec, section_html + "\n    " + sentinel_sec, 1)
        elif "</main>" in content:
            content = content.replace("</main>", section_html + "\n  </main>", 1)

        # Insert dropdown entry before sentinel (or fallback: before the closing </div> of dropdown-grid)
        sentinel_dd = "<!-- [[DROPDOWN_ITEMS_END]] -->"
        if sentinel_dd in content:
            content = content.replace(sentinel_dd, dropdown_html + "\n        " + sentinel_dd, 1)

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)

    # ── HTML builders ────────────────────────────────────────────────
    @staticmethod
    def _build_section_style(char):
        slug      = char["character"]
        theme     = char.get("theme", {})
        accent    = theme.get("accent", "#ffffff")
        atext     = theme.get("accentText", "#000000")
        bg        = theme.get("bg", "#111111")
        text      = theme.get("text", "#ffffff")
        muted     = theme.get("textMuted", "rgba(255,255,255,0.55)")
        border_c  = ShutdownableHandler._hex_to_rgba(accent, 0.50)
        return f"""  <style>
    #{slug} {{ background: {bg}; }}
    #{slug} .hero-eyebrow {{ color: {accent}; }}
    #{slug} .hero-title   {{ color: {text}; }}
    #{slug} .hero-tagline {{ color: {muted}; }}
    #{slug} .btn-primary  {{ background: {accent}; color: {atext}; }}
    #{slug} .btn-outline  {{ color: {accent}; border-color: {border_c}; }}
    #{slug} .stats-grid   {{ background: rgba(255,255,255,0.07); }}
    #{slug} .stat-card    {{ background: {bg}; }}
    #{slug} .stat-label   {{ color: {muted}; }}
    #{slug} .stat-value   {{ color: {text}; }}
    #{slug} .details-bio  {{ color: {muted}; }}
    #{slug} .btn-collapse {{ color: {accent}; border: 1.5px solid {border_c}; }}
  </style>"""

    @staticmethod
    def _build_section_html(char, bg_url):
        slug    = char["character"]
        title   = _h(char.get("title", slug))
        eyebrow = _h(char.get("eyebrow", ""))
        tagline = _h(char.get("tagline", ""))

        bg_divs = ""
        if bg_url:
            bg_divs = (
                f'\n      <div class="section-bg" style="background-image:url(\'{bg_url}\')"></div>'
                f'\n      <div class="section-overlay"></div>'
            )

        # Stats
        stats_html = ""
        for s in (char.get("stats") or []):
            stats_html += (
                f'\n            <div class="stat-card">'
                f'<span class="stat-label">{_h(s.get("label",""))}</span>'
                f'<span class="stat-value">{_h(s.get("value",""))}</span>'
                f'</div>'
            )

        # First two bio paragraphs
        bio_paras = [b for b in (char.get("bio") or []) if b.get("type") == "paragraph"][:2]
        bio_html = "".join(
            f'\n          <p class="details-bio">{_h(b.get("text",""))}</p>'
            for b in bio_paras
        )

        return f"""
    <!-- ================================================================
         {char.get('title','').upper()}  (added via Add Character)
    ================================================================ -->
    <section class="char-section" id="{slug}">{bg_divs}
      <div class="hero-content">
        <p class="hero-eyebrow">{eyebrow}</p>
        <h1 class="hero-title">{title}</h1>
        <p class="hero-tagline">{tagline}</p>
        <div class="hero-buttons">
          <button class="btn-primary" onclick="toggleDetails('{slug}-panel', this)">Learn More</button>
          <a class="btn-outline" href="characters/{slug}.html">View Character \u2197</a>
        </div>
      </div>

      <div class="details-panel" id="{slug}-panel">
        <div class="details-inner"><div class="details-content">
          <div class="stats-grid">{stats_html}
          </div>{bio_html}
          <button class="btn-collapse" onclick="toggleDetails('{slug}-panel', this)">Close \u2191</button>
        </div></div>
      </div>
    </section>"""

    @staticmethod
    def _build_dropdown_entry(char, bg_url):
        slug     = char["character"]
        title    = _h(char.get("title", slug))
        eyebrow  = char.get("eyebrow", "")
        universe = _h(eyebrow.split("·")[0].strip() if "·" in eyebrow else eyebrow)

        if bg_url:
            thumb = (
                f'<img class="dropdown-thumb" src="{bg_url}" '
                f'alt="{title}" loading="lazy" decoding="async">'
            )
        else:
            thumb = '<div class="dropdown-thumb-placeholder" aria-hidden="true">\u2605</div>'

        return f"""
        <a class="dropdown-char" href="characters/{slug}.html">
          {thumb}
          <span class="dropdown-name">{title}</span>
          <span class="dropdown-sub">{universe}</span>
        </a>"""

    # ── Colour helpers ───────────────────────────────────────────────
    @staticmethod
    def _contrast_text(hex_color):
        hx = hex_color.lstrip("#")
        if len(hx) == 3:
            hx = "".join(c * 2 for c in hx)
        try:
            r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if lum > 0.55 else "#ffffff"
        except Exception:
            return "#ffffff"

    @staticmethod
    def _hex_to_rgba(hex_color, alpha):
        hx = hex_color.lstrip("#")
        if len(hx) == 3:
            hx = "".join(c * 2 for c in hx)
        try:
            r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
            return f"rgba({r},{g},{b},{alpha})"
        except Exception:
            return f"rgba(255,255,255,{alpha})"

    # ── GET: inject heartbeat ────────────────────────────────────────
    def do_GET(self):
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
                pass
        return super().do_GET()

    def log_message(self, format, *args):
        pass

    # ── JSON response helpers ────────────────────────────────────────
    def _json_ok(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, code, message):
        body = json.dumps({"success": False, "error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def initiate_shutdown(self):
        with contextlib.suppress(Exception):
            self.shutdown()
            self.server_close()


def idle_monitor(server, timeout):
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
    httpd.last_ping = monotonic()
    threading.Thread(target=idle_monitor, args=(httpd, IDLE_TIMEOUT_SECONDS), daemon=True).start()
    return httpd


def main():
    ensure_index_exists()
    os.makedirs(os.path.join(project_root(), "images"), exist_ok=True)
    os.makedirs(os.path.join(project_root(), "data"),   exist_ok=True)

    print(f"🚀 Starting local server on http://localhost:{PORT}")
    httpd = serve(PORT)

    try:
        print("\n🧍 Available characters:")
        for name in list_characters():
            print(f" - {name}")

        url = f"http://localhost:{PORT}/index.html"
        print(f"\nOpening {url} in your browser...")
        webbrowser.open(url)

        print(f"\nℹ️  Server stops automatically when the page is idle for {IDLE_TIMEOUT_SECONDS}s.")
        print("   Routes:  POST /__save__           — persist character JSON")
        print("            POST /__upload__         — save photo to images/")
        print("            POST /__new_character__  — create new character (JSON + HTML + patches index)")
        httpd.serve_forever()
    finally:
        print("🛑 Server stopped.")
        with contextlib.suppress(Exception):
            httpd.server_close()


if __name__ == "__main__":
    main()
