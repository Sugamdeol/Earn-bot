import os
import time
import threading
import requests
import asyncio
from flask import Flask
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs

# --- CONFIGURATION ---
app = Flask(__name__)
DEFAULT_URL = "https://shortxlinks.com/Q0gNBbrR"

# --- HELPER: LOGGING (Taaki Render Logs mein turant dikhe) ---
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

# --- PART 2: Async Bot Logic (Jasoosi Mode) ---
async def run_bot_cycle():
    log("\n--- 🎬 New Cycle Start ---")
    
    target_link = get_final_link()
    
    if target_link:
        log(f"🔗 Target: {target_link}")
        log("⏳ 1 Minute wait (Skipping for testing if needed)...")
        # Testing ke liye 10 sec kar raha hu, production me 60 kar lena
        await asyncio.sleep(60)
        
        log("🖥️ Starting Browser...")
        try:
            async with async_playwright() as p:
                # Docker arguments
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                
                log("🚀 Opening CroxyProxy...")
                try:
                    await page.goto("https://www.croxyproxy.com", timeout=90000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # DEBUG: Title check karo
                    title = await page.title()
                    log(f"✅ Website Khul Gayi! Title: {title}")
                    
                except Exception as e:
                    log(f"❌ Proxy Site Load Fail: {e}")
                    await browser.close()
                    return

                # Input Box logic
                try:
                    # Input box dhoondne ki koshish
                    if await page.locator("#url").count() > 0:
                        await page.fill("#url", target_link)
                        log("✅ Input Box '#url' mil gaya.")
                    elif await page.locator("#request").count() > 0:
                        await page.fill("#request", target_link)
                        log("✅ Input Box '#request' mil gaya.")
                    else:
                        log("⚠️ Input box nahi mila! Page content check kar raha hu...")
                        # Agar fail ho, toh thoda HTML print karo taaki pata chale kya khula hai
                        content = await page.content()
                        log(f"DEBUG HTML: {content[:200]}") 
                        await browser.close()
                        return

                    log("➡️ Link daal diya, Enter daba raha hoon...")
                    await page.keyboard.press("Enter")
                    
                    # Wait for redirect
                    log("⏳ Redirect ka intezaar...")
                    await asyncio.sleep(10)
                    
                    # Check karo naya title kya hai
                    new_title = await page.title()
                    log(f"✅ Current Page Title: {new_title}")
                    
                    log("🛑 Holding 30s...")
                    await asyncio.sleep(30)
                    log("✅ Cycle Done!")
                    
                except Exception as e:
                    log(f"⚠️ Page Error: {e}")
                
                await browser.close()
        except Exception as e:
            log(f"❌ Browser Crash Error: {e}")
    else:
        log("⚠️ Link fail.")

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
    return "Jasoos Bot Active Hai! Logs Check Karo. 🕵️‍♂️"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

