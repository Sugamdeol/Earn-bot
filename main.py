
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

# --- 🌍 THE GIGANTIC PROXY LIST (60+ Unique Domains) ---
# Ye list alag-alag IP pools use karti hai.
ALL_PROXY_SITES = [
    # --- The Giants (High Success) ---
    "https://www.croxyproxy.com", "https://www.blockaway.net",
    "https://www.croxyproxy.rocks", "https://www.youtubeproxy.org",
    "https://www.croxy.net", "https://www.croxy.org",
    "https://www.croxyproxy.net", "https://www.hiload.org",
    "https://www.youtubeunblocked.live", "https://www.video-proxy.net",
    
    # --- The Generic Bunch ---
    "https://www.unblockvideos.com", "https://www.genmirror.com",
    "https://www.proxysite.site", "https://www.proxysite.one",
    "https://www.proxyium.com", "https://www.proxysite.cloud",
    "https://www.proxysite.video", "https://www.proxufy.com",
    
    # --- KProxy Family ---
    "https://www.kproxy.com", "https://server2.kproxy.com",
    "https://server3.kproxy.com", "https://server7.kproxy.com",
    
    # --- 4Ever & Hidester ---
    "https://www.4everproxy.com", "https://www.hidester.com/proxy",
    "https://www.filterbypass.me", "https://www.zalmos.com",
    
    # --- Old School PHP Proxies ---
    "https://www.megaproxy.com", "https://www.atozproxy.com",
    "https://www.justproxy.asia", "https://www.proxy-server.jp",
    "https://www.unblockmyweb.com", "https://www.sitenable.com",
    "https://www.sitenable.pw", "https://www.sitenable.top",
    "https://www.sitenable.info", "https://www.files.schools.edu.rs",
    
    # --- Random/New ---
    "https://www.wujie.net", "https://www.ninjaproxy.pw",
    "https://www.proxysite.li", "https://www.proxysite.cc",
    "https://www.unblock.club", "https://www.proxyportal.org",
    "https://www.proxyportal.net", "https://www.proxysite.us",
    "https://www.free-proxy.com", "https://www.sslproxy.com",
    "https://www.proxofree.com", "https://www.hotspotshield.com/proxy",
    "https://www.vpnbook.com/webproxy", "https://www.proxfree.com",
    "https://www.hide.me/en/proxy", "https://www.privatix.com",
    "https://www.tunnelbear.com", "https://www.windscribe.com",
    "https://www.zoogvpn.com", "https://www.turbohide.org",
    "https://www.zend2.com", "https://www.proxy.toolur.com"
]

# Shuffle kar do taaki pattern na bane
random.shuffle(ALL_PROXY_SITES)

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
    log("\n--- 🎬 New Cycle Start ---")
    
    target_link = get_final_link()
    
    if target_link:
        log(f"🔗 Target: {target_link}")
        
        # 1 Minute Break
        log(f"⏳ 60 Seconds ka break...")
        await asyncio.sleep(60)
        
        log("🖥️ Starting Browser...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                page = await browser.new_page()
                
                # --- SMART SELECTION LOGIC ---
                # List se ek site nikalo aur usko list ke end mein bhej do
                # Isse ensure hoga ki jab tak saari use nahi hoti, repetition nahi hoga
                current_proxy = ALL_PROXY_SITES.pop(0)
                ALL_PROXY_SITES.append(current_proxy) # Wapas peeche jod do
                
                log(f"🚀 Trying Proxy Site: {current_proxy}")
                
                try:
                    await page.goto(current_proxy, timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # --- UNIVERSAL INPUT FINDER (Har taale ki chabi) ---
                    input_found = False
                    
                    # Hum loop mein saare common selectors check karenge
                    selectors = [
                        "#url", "#request", "input[name='url']", 
                        "input[name='u']", "input[name='q']", 
                        "input[name='link']", "input[name='query']",
                        "#web_proxy_url", ".form-control"
                    ]
                    
                    for selector in selectors:
                        if await page.locator(selector).count() > 0:
                            # Safai: Agar pehle se kuch likha hai to clear karo
                            await page.locator(selector).fill("") 
                            await page.fill(selector, target_link)
                            input_found = True
                            log(f"✅ Input Box '{selector}' mil gaya.")
                            break
                    
                    if not input_found:
                        log("⚠️ Input box nahi mila (Design change?). Skip kar rahe hain.")
                        await browser.close()
                        return

                    log("➡️ Link daal diya, Go!")
                    await page.keyboard.press("Enter")
                    
                    # Redirect wait
                    log("⏳ Redirecting...")
                    await asyncio.sleep(15)
                    
                    new_title = await page.title()
                    log(f"✅ Page Title: {new_title}")
                    
                    # --- HOLD TIME (20s) ---
                    log("🛑 Holding connection for 20 seconds...")
                    await asyncio.sleep(20)
                    log("✅ Cycle Complete!")
                    
                except Exception as e:
                    log(f"❌ Site Error ({current_proxy}): {e}")
                
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
    return f"Bot Running! Pool Size: {len(ALL_PROXY_SITES)} sites. 🚜"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
