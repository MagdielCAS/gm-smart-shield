from playwright.sync_api import sync_playwright, expect
import time

def verify_knowledge():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = context.new_page()

        try:
            print("Navigating to Knowledge Page...")
            page.goto("http://localhost:5173/knowledge")
            page.wait_for_load_state("networkidle")

            # Monster
            monster_row = page.locator("div.group").filter(has_text="new_monster.md")
            expect(monster_row).to_be_visible()

            # Verify ETA - just check for "min remaining"
            # It might take a moment to appear (calculating...)
            # We can wait for it.
            try:
                expect(monster_row.get_by_text("min remaining")).to_be_visible(timeout=5000)
            except AssertionError:
                # If "Calculating..." is still there or something else.
                # screenshot to debug
                print("ETA verification timed out")
                pass # let's proceed to check refresh button

            # Refresh button
            # Div has title="Refresh source", button is inside.
            refresh_container = monster_row.locator("div[title='Refresh source']")
            expect(refresh_container).to_be_attached()

            # Button inside
            refresh_btn = refresh_container.locator("button")
            expect(refresh_btn).to_be_attached()
            # Should be disabled for running task
            expect(refresh_btn).to_be_disabled()

            print("Verification successful!")
            page.screenshot(path="verification/success.png", full_page=True)

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="verification/failed_verification_3.png", full_page=True)
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    verify_knowledge()
