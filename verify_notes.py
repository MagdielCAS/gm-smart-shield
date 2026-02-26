import time
from playwright.sync_api import sync_playwright

def verify_notes():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser error: {err}"))

        try:
            print("Navigating to notes page...")
            page.goto("http://localhost:5173/notes")

            # Wait for "Notes" heading
            print("Waiting for heading...")
            page.wait_for_selector("text=Notes", timeout=20000)

            # Create new note
            print("Creating new note...")
            page.click("button:has-text('New')")

            # Wait for editor
            print("Waiting for editor...")
            page.wait_for_selector("input[placeholder='Note Title']", timeout=10000)

            # Type title and content
            print("Typing content...")
            page.fill("input[placeholder='Note Title']", "Test Note")
            page.fill("textarea[placeholder='Start typing...']", "The party enters the Goblin Cave.")

            # Wait for auto-save (debounce 1s)
            print("Waiting for auto-save...")
            time.sleep(3)

            print("Taking screenshot...")
            page.screenshot(path="notes_verification.png")
            print("Screenshot saved to notes_verification.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="notes_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_notes()
