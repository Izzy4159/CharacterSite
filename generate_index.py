import os

CHARACTER_DIR = 'characters'
OUTPUT_FILE = 'index.html'

def generate_index():
    files = sorted(os.listdir(CHARACTER_DIR))
    html_links = []

    for file in files:
        if file.endswith('.html'):
            name = os.path.splitext(file)[0].capitalize()
            link = f'<li><a href="{CHARACTER_DIR}/{file}">{name}</a></li>'
            html_links.append(link)

    with open(OUTPUT_FILE, 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Favorite Characters</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <h1>Character Index</h1>
  <ul>
""")
        f.write('\n'.join(html_links))
        f.write("""
  </ul>
</body>
</html>
""")

    print(f"✅ index.html generated with {len(html_links)} characters.")

if __name__ == "__main__":
    generate_index()
