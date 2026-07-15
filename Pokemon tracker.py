import asyncio
import os
import datetime
import random
import json
from urllib.request import Request, urlopen
from playwright.async_api import async_playwright
from playwright_stealth import Stealth 

# ==================== CONFIGURATION ====================
TARGET_URL = "https://www.pokemoncenter.com/"
CHECK_INTERVAL_SECONDS = 600  

# 🛑 PASTE YOUR DISCORD WEBHOOK URL HERE:
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1519156442727190632/wYlmLQMw4ViMlj7bZdgTo6tj96iw8nArL3LQoRDJ-rDGNZFxaHRhjyZD0hmC37L75ajY"

QUEUE_URL_KEYWORDS = ["queue", "waitingroom", "queue-it"]
QUEUE_TEXT_INDICATORS = [
    "You are in the queue", 
    "Checking your browser", 
    "Line up", 
    "waiting room"
]

USER_DATA_DIR = os.path.join(os.getcwd(), "pokemon_browser_session")
# =======================================================

def send_discord_notification(message):
    """Sends a push notification alert to your phone via Discord Webhook."""
    if not DISCORD_WEBHOOK_URL or "YOUR_DISCORD" in DISCORD_WEBHOOK_URL:
        print("[Warning] Discord webhook URL not set up yet.")
        return

    payload = {"content": message}
    try:
        req = Request(
            DISCORD_WEBHOOK_URL, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urlopen(req) as response:
            if response.status == 204:
                print("📱 Push notification successfully sent to your phone!")
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

async def check_for_queue(page):
    current_url = page.url.lower()
    if any(keyword in current_url for keyword in QUEUE_URL_KEYWORDS):
        return True

    try:
        content = await page.content()
        if any(text.lower() in content.lower() for text in QUEUE_TEXT_INDICATORS):
            return True
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error reading page content: {e}")
        
    return False

async def monitor_site():
    print(f"[{datetime.datetime.now()}] Starting Pokémon Center Queue Monitor...")
    
    try:
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR)
    except Exception as e:
        print(f"Warning: Could not create directory {USER_DATA_DIR}: {e}")

    async with Stealth().use_async(async_playwright()) as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=True,  
                channel="chrome",
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        except Exception as launch_err:
            print(f"Persistent launch failed: {launch_err}. Trying standard launch...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

        page = context.pages[0] if context.pages else await context.new_page()

        # Track if we have already alerted so it doesn't spam your phone every single minute
        already_alerted = False

        try:
            while True:
                print(f"\n[{datetime.datetime.now()}] Checking site status...")
                try:
                    await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(3000)
                    
                    is_queue_active = await check_for_queue(page)
                    if is_queue_active:
                        print("🚨 ALERT: Queue is active!")
                        if not already_alerted:
                            send_discord_notification("🚨 **POKÉMON CENTER RESTOCK ALERT!** The queue page is officially live! Get to a computer! 🚨")
                            already_alerted = True
                    else:
                        print("Status: Normal (No queue detected).")
                        already_alerted = False # Reset so it can alert again on the next drop
                        
                except Exception as page_error:
                    print(f"Navigation error encountered: {page_error}")

                sleep_time = CHECK_INTERVAL_SECONDS + random.randint(-5, 10)
                print(f"Sleeping for {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            if 'browser' in locals():
                await browser.close()
            else:
                await context.close()

if __name__ == "__main__":
    try:
        asyncio.run(monitor_site())
    except KeyboardInterrupt:
        print("\nProgram closed safely.")