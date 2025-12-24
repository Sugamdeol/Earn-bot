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

# --- 🌍 THE ELITE LIST (Sirf Blockaway Family) ---
# Sirf wo sites jo Blockaway jaisa same engine use karti hain.
MASTER_PROXY_LIST = [
    "https://www.blockaway.net",        # Main Hero
    "https://www.croxyproxy.com",       # Big Brother
    "https://www.croxyproxy.rocks",
    "https://www.croxy.net",
    "https://www.croxy.org",
    "https://www.croxyproxy.net",
    "https://www.hiload.org",
    "https://www.youtubeunblocked.live",
    "https://www.video-proxy.net"
]

# --- WORKING LIST ---
# Is list mein se kharab sites nikalte jayenge
ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
random.shuffle(ACTIVE_PROXY_LIST)

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
            return None
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        return f"https://shortxlinks.com/Q0gNBbrR?{token}"
    except Exception as e:
        log(f"❌ Token Error: {e}")
        return None

# --- PART 2: Async Bot Logic ---
async def run_bot_cycle():
    global ACTIVE_PROXY_LIST
    
    log("\n--- 🎬 New Cycle Start (Elite Mode) ---")
    
    # Check agar list khali ho gayi
    if len(ACTIVE_PROXY_LIST) == 0:
        log("⚠️ Saari Blockaway sites fail ho gayi? List RELOAD kar raha hoon!")
        ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
        random.shuffle(ACTIVE_PROXY_LIST)

    target_link = get_final_link()
    
    if target_link:
        log(f"🔗 Target: {target_link}")
        
        log(f"⏳ 60 Seconds ka break...")
        await asyncio.sleep(60)
        
        log("🖥️ Starting Browser...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                
                # --- LIST HANDLING ---
                current_proxy = ACTIVE_PROXY_LIST.pop(0)
                
                log(f"🚀 Trying Elite Proxy: {current_proxy}")
                log(f"📉 Sites left in pool: {len(ACTIVE_PROXY_LIST)}")
                
                proxy_is_working = False 
                
                try:
                    await page.goto(current_proxy, timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # --- INPUT FINDER ---
                    input_found = False
                    
                    # Blockaway family ke common selectors
                    selectors = [
                        "#url", "#request", "input[name='url']", 
                        "#web_proxy_url", ".form-control"
                    ]
                    
                    for selector in selectors:
                        if await page.locator(selector).count() > 0:
                            await page.locator(selector).fill("") 
                            await page.fill(selector, target_link)
                            input_found = True
                            log(f"✅ Input Box '{selector}' mil gaya.")
                            break
                    
                    if not input_found:
                        log("⚠️ Input box nahi mila.")
                        await browser.close()
                        return # Working flag False hi rahega

                    log("➡️ Link daal diya, Go!")
                    await page.keyboard.press("Enter")
                    
                    log("⏳ Redirecting...")
                    await asyncio.sleep(15)
                    
                    new_title = await page.title()
                    log(f"✅ Page Title: {new_title}")
                    
                    proxy_is_working = True
                    
                    # --- HOLD TIME (20s) ---
                    log("🛑 Holding connection for 20 seconds...")
                    await asyncio.sleep(20)
                    log("✅ Cycle Complete!")
                    
                except Exception as e:
                    log(f"❌ Site Error ({current_proxy}): {e}")
                
                # --- FINAL DECISION ---
                if proxy_is_working:
                    ACTIVE_PROXY_LIST.append(current_proxy)
                    log(f"🌟 '{current_proxy}' pass ho gayi. Wapas team mein aaja!")
                else:
                    log(f"🗑️ '{current_proxy}' fail ho gayi. Isko bahar nikalo.")

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
    return f"Blockaway Elite Bot Running! Active Sites: {len(ACTIVE_PROXY_LIST)} 🚀"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
