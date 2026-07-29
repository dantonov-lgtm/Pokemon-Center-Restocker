import os
import time
import requests
from playwright.sync_api import sync_playwright

# Configuration
URL = "https://www.pokemoncenter.com/"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1519156442727190632/wYlmLQMw4ViMlj7bZdgTo6tj96iw8nArL3LQoRDJ-rDGNZFxaHRhjyZD0hmC37L75ajY"
CHECK_INTERVAL_SECONDS = 600 


def send_discord_alert(message: str):
    """Sends a notification message to your Discord channel via Webhook."""
    if DISCORD_WEBHOOK_URL == "https://discord.com/api/webhooks/1519156442727190632/wYlmLQMw4ViMlj7bZdgTo6tj96iw8nArL3LQoRDJ-rDGNZFxaHRhjyZD0hmC37L75ajY":
        print("[WARNING] Discord Webhook URL is not configured. Skipping alert.")
        return

    data = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code in (200, 204):
            print("Successfully sent alert to Discord!")
        else:
            print(f"Failed to send Discord alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending Discord alert: {e}")


def check_queue():
    """Launches Playwright to inspect the target page for queue indicators."""
    with sync_playwright() as p:
        # Launch Chromium browser
        browser = p.chromium.launch(
            headless=True,  # Set to False if you want to watch the browser window
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        # Create a browser context with a realistic user-agent string
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720}
        )

        page = context.new_page()

        print("Starting Pokémon Center Queue Monitor...")
        print(f"Monitoring: {URL}\nPress Ctrl+C in terminal to stop.\n")

        queue_alert_sent = False

        while True:
            try:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking page status...")
                
                # Navigate to the site
                page.goto(URL, wait_until="domcontentloaded", timeout=30000)
                
                # Extract inner text of the body tag
                body_text = page.inner_text("body").lower()

                # Queue detection triggers
                queue_phrases = [
                    "virtual queue to enter",
                    "you're in the virtual queue",
                    "you are in line",
                    "estimated wait time"
                ]

                # Check if any queue phrase exists on the page
                is_in_queue = any(phrase in body_text for phrase in queue_phrases) or "queue" in page.url.lower()

                if is_in_queue:
                    print("🚨 QUEUE DETECTED!")
                    
                    # Avoid spamming Discord on every loop pass while the queue remains live
                    if not queue_alert_sent:
                        send_discord_alert("🚨 **Pokémon Center Queue is LIVE!** Get in line now!\n" + URL)
                        queue_alert_sent = True
                else:
                    print("No queue detected. Page loaded normally.")
                    queue_alert_sent = False  # Reset flag when queue clears

            except Exception as e:
                print(f"An error occurred during check: {e}")

            # Wait before running the next check
            time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    check_queue()