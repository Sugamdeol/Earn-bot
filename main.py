
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

# BEAST SETTING: Ek saath kitne tab kholne hain?
# Render Free Plan ke liye 3 se zyada mat karna, crash ho jayega.
CONCURRENT_HITS = 3 

# --- 🌍 THE GIGANTIC PROXY LIST ---
ALL_PROXY_SITES = [
    "https://www.croxyproxy.com", "https://www.blockaway.net",
    "https://www.croxyproxy.rocks", "https://www.youtubeproxy.org",
    "https://www.croxy.net", "https://www.croxy.org",
    "https://www.croxyproxy.net", "https://www.hiload.org",
    "https://www.youtubeunblocked.live", "https://www.video-proxy.net",
    "https://www.unblockvideos.com", "https://www.genmirror.com",
    "https://www.proxysite.site", "https://www.proxysite.one",
    "https://www.proxyium.com", "https://www.proxysite.cloud",
    "https://www.proxysite.video", "https://www.proxufy.com",
    "https://www.kproxy.com", "https://server2.kproxy.com",
    "https://www.4everproxy.com", "https://www.hidester.com/proxy",
    "https://www.filterbypass.me", "https://www.zalmos.com",
    "https://www.megaproxy.com", "https://www.atozproxy.com",
    "https://www.justproxy.asia", "https://www.proxy-server.jp",
    "https://www.unblockmyweb.com", "https://www.sitenable.com",
    "https://www.sitenable.pw", "https://www.sitenable.top",
    "https://www.wujie.net", "https://www.ninjaproxy.pw",
    "https://www.proxysite.li", "https://www.proxysite.cc",
    "https://www.unblock.club", "https://www.proxyportal.org",
    "https://www.proxyportal.net", "https://www.proxysite.us"
]
random.shuffle(ALL_PROXY_SITES)

# --- HELPER: LOGGING ---
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

# --- PART 1: Token Logic (Har hit ke liye naya token) ---
def get_fresh_token():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r1 = requests.get(DEFAULT_URL, headers=headers, allow_redirects=False)
        
        if "location" not in r1.headers: return None
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        return f"https://shortxlinks.com/Q0gNBbrR?{token}"
    except Exception:
        return None

# --- PART 2: Single Hit Logic (Ek Sipahi ka kaam) ---
async def process_single_hit(browser, hit_id):
    # Har worker apna khud ka token aur proxy lega
    target_link = get_fresh_token()
    if not target_link:
        log(f"⚠️ [Worker {hit_id}] Token generate nahi hua.")
        return

    # List se proxy nikalo aur peeche jod do (Rotation)
    proxy_url = ALL_PROXY_SITES.pop(0)
    ALL_PROXY_SITES.append(proxy_url)
    
    log(f"⚔️ [Worker {hit_id}] Target: ...{target_link[-10:]} | Via: {proxy_url}")
    
    page = await browser.new_page()
    try:
        await page.goto(proxy_url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        
        # Input Logic
        input_found = False
        selectors = ["#url", "#request", "input[name='url']", "input[name='u']", "input[name='q']", "#web_proxy_url"]
        
        for selector in selectors:
            if await page.locator(selector).count() > 0:
                await page.locator(selector).fill("") 
                await page.fill(selector, target_link)
                input_found = True
                break
        
        if not input_found:
            log(f"⚠️ [Worker {hit_id}] Input box nahi mila on {proxy_url}")
            await page.close()
            return

        await page.keyboard.press("Enter")
        
        # Redirect Wait
        await asyncio.sleep(15)
        
        # Hold Logic (20s)
        log(f"🛑 [Worker {hit_id}] Holding for 20s...")
        await asyncio.sleep(20)
        
        title = await page.title()
        log(f"✅ [Worker {hit_id}] Done! Title: {title}")
        
    except Exception as e:
        log(f"❌ [Worker {hit_id}] Fail: {e}")
    
    await page.close()

# --- PART 3: The Beast Orchestrator (Manager) ---
async def run_beast_mode():
    log("\n--- 🔥 BEAST MODE STARTED ---")
    
    # Wait at start
    log("⏳ 60 Seconds ka break (System thanda karne ke liye)...")
    await asyncio.sleep(60)
    
    log(f"🖥️ Launching Browser for {CONCURRENT_HITS} Simultaneous Hits...")
    
    try:
        async with async_playwright() as p:
            # Browser ek hi rahega, Tabs (Pages) alag alag honge memory bachane ke liye
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            
            # Tasks ki list banao
            tasks = []
            for i in range(CONCURRENT_HITS):
                # Har task ko ek ID de diya
                tasks.append(process_single_hit(browser, i+1))
            
            # BOOM! Sabko ek saath run karo
            log("🚀 Launching All Missiles...")
            await asyncio.gather(*tasks)
            
            log("🏁 Batch Complete! Closing Browser.")
            await browser.close()
            
    except Exception as e:
        log(f"❌ Critical Error: {e}")

# Wrapper for Thread
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            loop.run_until_complete(run_beast_mode())
        except Exception as e:
            log(f"❌ Loop Error: {e}")
            
        log("💤 10s Rest...")
        time.sleep(10)

# --- PART 4: Server ---
@app.route('/')
def home():
    return f"Beast Mode Active! Hits per cycle: {CONCURRENT_HITS} 🦍"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
