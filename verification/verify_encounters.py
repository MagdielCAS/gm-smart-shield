import json
from playwright.sync_api import sync_playwright

def verify_encounters_page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Print console logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))

        # Mock the API response
        mock_response = {
            "title": "Ambush at the Murky Crossing",
            "description": "The party approaches a rickety wooden bridge...",
            "tactics": "The shaman stays back...",
            "loot": "A pouch with 50gp...",
            "npcs": []
        }

        page.route("**/api/v1/encounters/generate", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_response)
        ))

        # Navigate
        print("Navigating to Encounters page...")
        page.goto("http://localhost:5174/encounters")

        # Wait for something basic to load
        try:
            page.wait_for_selector("text=Encounter Generator", timeout=5000)
            print("Found header 'Encounter Generator'")
        except:
            print("Header not found. Taking debug screenshot.")
            page.screenshot(path="/app/verification/debug_blank.png")
            # Dump HTML
            with open("/app/verification/debug.html", "w") as f:
                f.write(page.content())
            browser.close()
            return

        # Take screenshot of initial state
        page.screenshot(path="/app/verification/encounters_initial.png")
        print("Initial screenshot taken.")

        # Fill form
        print("Filling form...")
        page.fill("textarea", "Swamp ambush")
        page.fill("input[type=number]", "3")
        page.select_option("select", "Hard")

        print("Clicking Generate...")
        page.click("button[type=submit]")

        page.wait_for_selector("text=Ambush at the Murky Crossing")

        page.screenshot(path="/app/verification/encounters_result.png")
        print("Result screenshot taken.")

        browser.close()

if __name__ == "__main__":
    verify_encounters_page()
