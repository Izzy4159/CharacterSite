# Character Showcase Site

A locally-hosted character profile site built with pure Python and vanilla JS. Each character gets a full-viewport section on the homepage with a faded background image, animated Ken Burns effect, expandable bio panel, and a dedicated profile page. Everything is editable from localhost — background images, fonts, colors, gallery photos, and text — while visitors on the local network see a clean read-only version.

---

## Screenshots

_Drop screenshots in here once the site is running._

**Homepage**
![Homepage](screenshots/homepage.png)

**Character Section (expanded)**
![Character Section](screenshots/section-expanded.png)

**Individual Character Page**
![Character Page](screenshots/character-page.png)

**Edit Mode**
![Edit Mode](screenshots/edit-mode.png)

**Background Image Upload Modal**
![BG Modal](screenshots/bg-modal.png)

**Style Customization Modal**
![Style Modal](screenshots/style-modal.png)

**Mobile View**
![Mobile](screenshots/mobile.png)

---

## Features

### Homepage
- **Full-viewport character sections** — each character occupies 100vh with a faded, parallax-ready background image and a layered dark overlay
- **Ken Burns animation** — background images slowly pan and zoom while the section is on screen, restarting each time it scrolls back into view via IntersectionObserver
- **Hover expand** — hovering a section on desktop briefly expands it; clicking Learn More fully opens a detail panel with bio text and stats
- **Learn More / Close panel** — expandable accordion panel per section with smooth animation; scrolls into view automatically when opened
- **View Character button** — links to the individual character profile page
- **Browse dropdown nav** — sticky top nav with a mega-dropdown showing thumbnail previews of all characters and direct links to their pages
- **Copy Link button** — copies the local network URL (e.g. `http://192.168.1.x:8000`) to your clipboard so you can share it with anyone on the same WiFi; shows a brief "Copied!" confirmation

### Individual Character Pages
- **Hero section** — large title, eyebrow label (universe + year), and tagline pulled from the character's JSON data file
- **Photo gallery** — CSS masonry columns layout with lazy-loaded images; supports any number of photos
- **Stats grid** — clean grid of label/value pairs (real name, affiliation, abilities, etc.)
- **Bio sections** — alternating headings and paragraphs rendered from structured JSON

### Edit Mode (localhost only)
- **In-place text editing** — click the pencil FAB to enter edit mode; title, tagline, eyebrow, stats, and bio become directly editable with a styled contenteditable outline
- **Background image upload** — drag and drop an image (or click to browse) into the modal; live preview before confirming; saves as `bg.<ext>` and cache-busts the URL on every upload so the browser always shows the new image
- **Font and color customization** — style modal per section lets you pick a font (Inter, Playfair Display, Merriweather, Space Mono, Dancing Script, Bebas Neue, Oswald) and set title color, tagline color, and accent color with live preview
- **Photo gallery management** — upload additional photos to a character's gallery in edit mode; delete photos with the × button
- **Add New Character** — floating + button opens a form to create a brand new character: name, tagline, universe/year label, accent color, optional background image, and a starting bio; the server auto-generates the HTML page, JSON data file, and image folder, then patches the homepage in-place so the new section is immediately visible on refresh
- **Save** — all edits (text, stats, bio) are saved to the character's JSON file via a POST to the local server

### Sharing & Network
- **LAN access** — server binds to `0.0.0.0` so anyone on the same WiFi can open the site using the network URL printed at startup
- **View-only for network visitors** — all edit controls (left-side buttons, Add Character FAB, edit FAB, upload buttons, modals) are hidden for anyone not on localhost; enforced at two layers: the server injects `window._IS_LOCAL` and applies a CSS class before the page paints, and JS double-checks `location.hostname` as a fallback
- **Copy Link button** — one click to copy the network URL; uses `navigator.clipboard` with an `execCommand` fallback for non-secure contexts

### Layout & Responsiveness
- **Mobile responsive** — fluid typography with `clamp()`, responsive grid and column breakpoints at 900px, 540px, and 380px
- **Touch-friendly** — hover interactions (section expand, left-side edit buttons) have `:active` fallbacks for touch devices via `@media (hover: none)`
- **Viewport meta** — all pages include a proper `<meta name="viewport">` tag

### Server
- **Auto-shutdown** — server monitors for page heartbeat pings (sent every 5 seconds by the browser); shuts down automatically after 20 seconds of inactivity
- **No dependencies** — runs entirely on Python's standard library; nothing to install

---

## Project Structure

```
CharacterSite/
├── launch_site.py        # Python HTTP server — serves files, handles all POST routes
├── index.html            # Homepage — all character sections, nav, modals, inline JS/CSS
├── character.css         # Shared styles for individual character pages
├── character.js          # Shared JS for individual character pages (render, edit, save)
│
├── characters/           # One HTML file per character (all identical shell templates)
│   ├── batman.html
│   ├── sasuke.html
│   ├── masterchief.html
│   ├── erenjager.html
│   └── zuko.html
│
├── data/                 # Character data — one JSON file per character
│   ├── batman.json
│   ├── sasuke.json
│   ├── masterchief.json
│   ├── erenjager.json
│   └── zuko.json
│
└── images/               # Uploaded images — one subfolder per character
    ├── Batman/
    ├── Sasuke/
    ├── erenjager/
    ├── masterchief/
    └── Zuko/
```

**Key files explained:**

| File | What it does |
|---|---|
| `launch_site.py` | Custom HTTP server. Handles GET (serves files, injects JS globals into HTML), and POST routes for saving JSON, uploading images, creating characters, setting backgrounds, and setting styles |
| `index.html` | Self-contained homepage with all CSS inline. Reads character data from the DOM (injected by `launch_site.py` on first render / patched in-place on edits) |
| `character.js` | Fetches `../data/<slug>.json`, renders the hero/gallery/stats/bio, wires up edit mode, photo upload, and save |
| `character.css` | Styles shared across all character profile pages |
| `data/*.json` | Source of truth for each character's content (title, bio, stats, theme, image list, background URL) |

---

## How to Run

Python 3.8+ is required. No packages to install.

```bash
cd CharacterSite
python launch_site.py
```

The server starts on port **8000**, opens the homepage in your default browser automatically, and prints both URLs:

```
🚀 Starting local server...
   Local:   http://localhost:8000
   Network: http://192.168.1.x:8000  ← share this link on your WiFi
```

The server shuts itself down automatically after 20 seconds of inactivity (no open browser tabs pinging it).

---

## How to Add a New Character

1. On the homepage, click the **+** floating button in the bottom-right corner (only visible from localhost)
2. Fill in the form:
   - **Character Name** — used as the page title and to generate the URL slug
   - **Tagline** — short one-liner shown under the name
   - **Universe & Year** — eyebrow label, e.g. `DC Comics · 1939`
   - **Accent Color** — used for buttons and highlights on the character's section
   - **Background Image** — optional; drag in a photo or click to browse
   - **Bio** — opening paragraph for the character's profile
3. Click **Create Character**

The server will:
- Create `characters/<slug>.html`
- Create `data/<slug>.json`
- Create `images/<slug>/` (and save the background image if provided)
- Patch `index.html` to add the new section — visible immediately on next page load

To add more detail (stats, additional bio paragraphs, more photos), visit the character's profile page and use edit mode there.

---

## How to Edit a Character

### Changing the background image

1. Hover over a character section on the homepage — two small buttons appear on the left edge
2. Click the **image icon** (mountain/sun icon)
3. Drag a new image into the drop zone, or click **Choose file**
4. Check the live preview, then click **Set Background**

The image is saved as `bg.<ext>` in the character's image folder and the homepage is updated immediately with a cache-busted URL.

### Changing fonts and colors

1. Hover the character section and click the **palette icon** (left-side buttons)
2. Choose a font from the dropdown — preview updates live
3. Pick title color, tagline color, and accent color with the color pickers
4. Click **Apply Style**

Styles are saved to the character's JSON and patched into `index.html` as a `<style>` block so they survive page refresh.

### Editing text and stats on a character's profile page

1. Go to the character's profile page (click **View Character**)
2. Click the **pencil FAB** (bottom-right)
3. Edit any text directly — title, tagline, eyebrow, stats labels/values, and bio paragraphs all become editable
4. Click **Save Changes** — data is written to `data/<slug>.json`

### Adding or removing gallery photos

1. Enter edit mode on the character's profile page (pencil FAB)
2. Click **+ Add Photo** and select one or more images
3. To remove a photo, click the **×** button that appears on each image in edit mode
4. Save when done

---

## Sharing the Site

1. Start the server — the network URL is printed in the terminal at startup
2. Click **Copy Link** in the top nav (or read the URL from the terminal)
3. Open that URL on any device connected to the same WiFi network

Visitors on the network URL see the full site — all content, animations, navigation, and character pages — but with all editing controls hidden. They can browse, read, and navigate but cannot modify anything.

---

## Tech Stack

| Technology | Role |
|---|---|
| Python 3 (stdlib only) | HTTP server, file I/O, POST route handling, HTML patching |
| `http.server` + `socketserver` | Base server with threading support |
| HTML5 | Page structure for homepage and character pages |
| CSS3 | Inline styles in `index.html`, shared `character.css`; uses `clamp()`, CSS columns, custom properties, `@media` queries |
| Vanilla JavaScript | All interactivity — rendering, edit mode, modals, upload, save, copy link, Ken Burns, IntersectionObserver |
| Google Fonts | Inter, and optional per-character fonts loaded on demand |

No build step, no package manager, no frameworks.

---

## Notes

- **Edit controls are only visible from `localhost` or `127.0.0.1`** — anyone accessing the site via the network IP sees a clean view-only version with no edit buttons, no modals, and no FABs. This is enforced by both the server (which injects `window._IS_LOCAL` before the page renders) and a client-side fallback that checks `window.location.hostname`.
- Character slugs are generated by stripping all non-alphanumeric characters from the name (e.g. `"Master Chief"` → `masterchief`). The image folder uses a hyphenated version (e.g. `master-chief`).
- Background images are always saved as `bg.<ext>`, overwriting the previous one. Gallery photos keep their original filenames with a counter suffix if there's a collision.
- The `data/*.json` files are the source of truth. If you ever want to manually edit a character's content, just edit the JSON directly and reload the page.
