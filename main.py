
import os
import time
import threading
import requests
import asyncio
import random
from flask import Flask
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs

# --- CONFIGURATION ---
app = Flask(__name__)
DEFAULT_URL = "https://shortxlinks.com/Q0gNBbrR"

# --- PROXY LIST (Dukaanon ki List) ---
# Hum inme se har baar ek alag site pick karenge
PROXY_SITES = [
    "https://www.croxyproxy.com",
    "https://www.blockaway.net",
    "https://www.croxyproxy.rocks",
    "https://www.youtubeproxy.org"
]

# --- HELPER: LOGGING ---
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

# --- PART 1: Token Logic ---
def get_final_link():
    try:
        log("🔍 Token dhoondh raha hoon...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        r1 = requests.get(DEFAULT_URL, headers=headers, allow_redirects=False)
        
        if "location" not in r1.headers: 
            log("❌ Redirect location nahi mili.")
            return None
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        
        if "adlinkfly" not in query:
            log("❌ adlinkfly parameter nahi mila.")
            return None

        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        return f"https://shortxlinks.com/Q0gNBbrR?{token}"
    except Exception as e:
        log(f"❌ Token Error: {e}")
        return None

# --- PART 2: Async Bot Logic (Rotation Wala) ---
async def run_bot_cycle():
    log("\n--- 🎬 New Cycle Start ---")
    
    target_link = get_final_link()
    
    if target_link:
        log(f"🔗 Target: {target_link}")
        
        # Random Wait before start (10-60 sec)
        wait_time = 60 # Aapne 1 min bola tha
        log(f"⏳ {wait_time} Seconds ka break (Link pakne do)...")
        await asyncio.sleep(wait_time)
        
        log("🖥️ Starting Browser...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                
                # --- ROTATION LOGIC ---
                # List mein se koi ek random site uthao
                selected_proxy = random.choice(PROXY_SITES)
                log(f"🚀 Aaj ki sawari: {selected_proxy}")
                
                try:
                    await page.goto(selected_proxy, timeout=90000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    title = await page.title()
                    log(f"✅ Proxy Site Open: {title}")
                    
                except Exception as e:
                    log(f"❌ Site Load Fail ({selected_proxy}): {e}")
                    await browser.close()
                    return

                # --- INPUT LOGIC (Sab sites ke liye common jugad) ---
                try:
                    # Zyada tar sites pe ID 'url' ya 'request' hi hoti hai
                    if await page.locator("#url").count() > 0:
                        await page.fill("#url", target_link)
                        log("✅ Input Box '#url' mil gaya.")
                    elif await page.locator("#request").count() > 0:
                        await page.fill("#request", target_link)
                        log("✅ Input Box '#request' mil gaya.")
                    elif await page.locator("input[name='url']").count() > 0:
                         await page.fill("input[name='url']", target_link)
                         log("✅ Input Box 'name=url' mil gaya.")
                    else:
                        log("⚠️ Input box nahi mila! HTML check kar raha hu...")
                        content = await page.content()
                        log(f"DEBUG HTML: {content[:200]}")
                        await browser.close()
                        return

                    log("➡️ Link daal diya, Go!")
                    await page.keyboard.press("Enter")
                    
                    # Redirect wait
                    log("⏳ Redirecting...")
                    await asyncio.sleep(10)
                    
                    new_title = await page.title()
                    log(f"✅ Page Title: {new_title}")
                    
                    # --- HOLD TIME (Updated to 20s) ---
                    log("🛑 Holding connection for 20 seconds...")
                    await asyncio.sleep(20)
                    log("✅ Cycle Complete!")
                    
                except Exception as e:
                    log(f"⚠️ Page Error: {e}")
                
                await browser.close()
        except Exception as e:
            log(f"❌ Browser Crash: {e}")
    else:
        log("⚠️ Token nahi mila.")

# Wrapper for Thread
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            loop.run_until_complete(run_bot_cycle())
        except Exception as e:
            log(f"❌ Loop Error: {e}")
            
        log("💤 10s Rest...")
        time.sleep(10)

# --- PART 3: Server ---
@app.route('/')
def home():
    return "Bot is Rotating Proxies! 🔄"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
