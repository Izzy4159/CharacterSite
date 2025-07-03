# CharacterSite
# 🧍 Character Showcase Site

Welcome to the **Character Showcase Site**, a simple, fast, and visually themed project that lets users explore detailed profiles of fictional characters like Batman and Sasuke Uchiha. Each character has their own custom-designed page with unique styling, color themes, and floating images — all served locally using Python.

---

## 🌟 Features

- 🎨 **Custom Themed Pages**  
  Each character has a uniquely styled HTML page reflecting their personality or origin (e.g. dark & bold for Batman, light purple tones for Sasuke).

- 🖼️ **Fast Image Loading with `lazy` Support**  
  Character images use `loading="lazy"` for better performance and snappy load times.

- 🧠 **CSS Class Overrides for Each Character**  
  The CSS uses `.batman`, `.sasuke-page`, and other class-based overrides for full control over look and feel.

- 💡 **Simple Local Python Server**  
  Just run `launch_site.py`, type a character’s name or `'m'` for the main index, and view it instantly in your browser.

- 💻 **Clean Structure, No Frameworks**  
  Pure HTML, CSS, and Python — easy to edit, expand, or deploy anywhere.

---

## 🧰 Tech Stack

| Technology   | Purpose                              |
|--------------|--------------------------------------|
| `HTML5`      | Markup for each character page       |
| `CSS3`       | Styling, colors, fonts, and layout   |
| `Python`     | Launches a simple local HTTP server  |
| `Threading`  | Background server while you choose   |
| `Webbrowser` | Opens your default browser with the page |

---

## ▶️ How to Launch

1. Ensure Python 3.x is installed.
2. From the root folder, run:

   ```bash
   python launch_site.py
3. Follow the prompt:
 - Type m to open the main index page
 - Type a character name (e.g., sasuke) to open their profile

4. Press Enter to stop the server when you're done.

## 🗂️ Project Structure

character-showcase/
├── index.html            # Main homepage with character links
├── styles.css            # Global and themed CSS styles
├── launch_site.py        # Local server + launcher script
└── characters/
    ├── batman.html       # Batman’s profile page
    └── sasuke.html       # Sasuke Uchiha’s profile page

## 🎨 Adding More Characters

- **To add a new character:**

1. Create a new .html file in the /characters directory.
2. Use <body class="your-character-page"> to enable CSS overrides.
3. Add .your-character styles in styles.css (background, hover, font).
4. Update index.html to include a new <a> link with class="character-link your-character".


