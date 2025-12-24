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

# --- 🌍 MEGA PROXY LIST (30+ Sites) ---
# Ab pakadna namumkin hai!
PROXY_SITES = [
    # --- Croxy Family ---
    "https://www.croxyproxy.com",
    "https://www.croxyproxy.rocks",
    "https://www.croxy.net",
    "https://www.croxy.org",
    "https://www.croxyproxy.net",
    # --- Blockaway Family ---
    "https://www.blockaway.net",
    "https://www.hiload.org",
    # --- Video Proxies ---
    "https://www.youtubeunblocked.live",
    "https://www.video-proxy.net",
    "https://www.unblockvideos.com",
    "https://www.youtubeproxy.org",
    "https://www.genmirror.com",
    # --- Classic Proxies ---
    "https://www.4everproxy.com",
    "https://www.kproxy.com",
    "https://www.filterbypass.me",
    "https://www.proxysite.site",
    "https://www.proxysite.one",
    "https://www.proxyium.com",
    "https://www.proxysite.cloud",
    "https://www.zalmos.com",
    "https://www.megaproxy.com",
    "https://www.atozproxy.com",
    # --- New/Random ---
    "https://www.hidden.in",
    "https://www.sitenable.com",
    "https://www.sitenable.pw",
    "https://www.sitenable.top",
    "https://www.unblockmyweb.com",
    "https://www.proxy-server.jp",
    "https://www.wujie.net",
    "https://www.ninjaproxy.pw"
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
        
        # 1 Minute Break
        wait_time = 60 
        log(f"⏳ {wait_time} Seconds ka break (Link pakne do)...")
        await asyncio.sleep(wait_time)
        
        log("🖥️ Starting Browser...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                
                # --- ROTATION LOGIC ---
                selected_proxy = random.choice(PROXY_SITES)
                log(f"🚀 Aaj ki sawari: {selected_proxy}")
                
                try:
                    await page.goto(selected_proxy, timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    title = await page.title()
                    log(f"✅ Proxy Site Open: {title}")
                    
                except Exception as e:
                    log(f"❌ Site Load Fail ({selected_proxy}): {e}")
                    await browser.close()
                    return

                # --- ADVANCED INPUT LOGIC (Har type ka lock kholne ki chabi) ---
                try:
                    input_found = False
                    
                    # 1. ID Check (Sabse common)
                    if await page.locator("#url").count() > 0:
                        await page.fill("#url", target_link)
                        input_found = True
                        log("✅ Input Box '#url' mil gaya.")
                        
                    # 2. Request ID (Blockaway)
                    elif await page.locator("#request").count() > 0:
                        await page.fill("#request", target_link)
                        input_found = True
                        log("✅ Input Box '#request' mil gaya.")
                        
                    # 3. Name = url (Generic)
                    elif await page.locator("input[name='url']").count() > 0:
                         await page.fill("input[name='url']", target_link)
                         input_found = True
                         log("✅ Input Box 'name=url' mil gaya.")

                    # 4. Name = u (KProxy/4everproxy style)
                    elif await page.locator("input[name='u']").count() > 0:
                         await page.fill("input[name='u']", target_link)
                         input_found = True
                         log("✅ Input Box 'name=u' mil gaya.")

                    # 5. Name = q (Old PHP Proxy style)
                    elif await page.locator("input[name='q']").count() > 0:
                         await page.fill("input[name='q']", target_link)
                         input_found = True
                         log("✅ Input Box 'name=q' mil gaya.")
                    
                    if not input_found:
                        log("⚠️ Input box nahi mila! Site ka design alag hai.")
                        await browser.close()
                        return

                    log("➡️ Link daal diya, Go!")
                    await page.keyboard.press("Enter")
                    
                    # Redirect wait
                    log("⏳ Redirecting...")
                    await asyncio.sleep(10)
                    
                    new_title = await page.title()
                    log(f"✅ Page Title: {new_title}")
                    
                    # --- HOLD TIME (20s) ---
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
    return "Bot is running on 30+ Proxy Sites! 🌍"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
