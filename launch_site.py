import http.server
import socketserver
import webbrowser
import os
import threading

CHARACTER_DIR = "characters"
PORT = 8000

def list_characters():
    try:
        files = os.listdir(CHARACTER_DIR)
        html_files = [f for f in files if f.endswith('.html')]
        return [os.path.splitext(f)[0] for f in html_files]
    except FileNotFoundError:
        return []

def main():
    print("🚀 Starting local server on port 8000...")
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)

    # Start the server in the background
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    print("\n🧍 Available characters:")
    characters = list_characters()
    for name in characters:
        print(f" - {name}")

    print("\n🔹 Type a character name to view their page")
    print("🔹 Type 'm' to open the main index page")

    choice = input("\nWhich page do you want to open? ").strip().lower()

    if not choice:
        print("❌ No input detected.")
        httpd.shutdown()
        return

    if choice == "m":
        url = f"http://localhost:{PORT}/index.html"
        print(f"Opening main index page: {url}")
        webbrowser.open(url)
    else:
        filename = f"{CHARACTER_DIR}/{choice}.html"
        if os.path.exists(filename):
            url = f"http://localhost:{PORT}/{filename}"
            print(f"Opening {url} in your browser...")
            webbrowser.open(url)
        else:
            print(f"❌ Character page '{choice}.html' not found.")

    input("\nPress Enter to stop the server and exit...")
    httpd.shutdown()

if __name__ == "__main__":
    main()
