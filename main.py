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

# --- 🌍 WEB PROXY LIST (For 2 Web Hits) ---
WEB_PROXY_SITES = [
    "https://www.croxyproxy.com", "https://www.blockaway.net",
    "https://www.croxyproxy.rocks", "https://www.youtubeproxy.org",
    "https://www.croxy.net", "https://www.croxy.org",
    "https://www.hiload.org", "https://www.youtubeunblocked.live",
    "https://www.proxysite.site", "https://www.proxysite.one",
    "https://www.proxyium.com", "https://www.proxysite.cloud",
    "https://www.kproxy.com", "https://www.4everproxy.com",
    "https://www.filterbypass.me", "https://www.zalmos.com",
    "https://www.megaproxy.com", "https://www.atozproxy.com"
]
random.shuffle(WEB_PROXY_SITES)

# --- 📡 DIRECT PROXY LIST (Will be filled by API) ---
DIRECT_PROXIES = []

# --- HELPER: LOGGING ---
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

# --- PART 1: Token Logic ---
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

# --- PART 2: Geonode API Fetcher ---
def fetch_geonode_proxies():
    global DIRECT_PROXIES
    api_url = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    try:
        log("📡 Fetching Fresh Proxies from Geonode API...")
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            new_proxies = []
            for item in data.get("data", []):
                ip = item["ip"]
                port = item["port"]
                protocols = item["protocols"]
                
                # Hum prefer karenge HTTP/HTTPS proxies
                if "http" in protocols or "https" in protocols:
                    proxy_str = f"http://{ip}:{port}"
                    new_proxies.append(proxy_str)
            
            DIRECT_PROXIES = new_proxies
            log(f"✅ Loaded {len(DIRECT_PROXIES)} fresh proxies from API.")
        else:
            log("❌ API Fail. Using old list if available.")
    except Exception as e:
        log(f"❌ API Error: {e}")

# --- TASK A: Direct Hit (Using Geonode Proxy) ---
async def task_direct_hit(browser, hit_id):
    target_link = get_fresh_token()
    if not target_link: return

    # API wali list se proxy nikalo
    if not DIRECT_PROXIES:
        log(f"⚠️ [Worker {hit_id}] No Direct Proxies available!")
        return
        
    proxy_server = random.choice(DIRECT_PROXIES)
    log(f"⚔️ [Worker {hit_id}] DIRECT HIT via {proxy_server}")

    # Naya Context (Identity) banao specific proxy ke saath
    try:
        context = await browser.new_context(
            proxy={"server": proxy_server},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        # Attack
        try:
            await page.goto(target_link, timeout=45000) # 45s timeout for slow proxies
            await page.wait_for_load_state("domcontentloaded")
            
            # Wait 20s
            log(f"🛑 [Worker {hit_id}] Direct Hit Connected! Holding 20s...")
            await asyncio.sleep(20)
            
            title = await page.title()
            log(f"✅ [Worker {hit_id}] Direct Success! Title: {title}")
            
        except Exception as e:
            log(f"❌ [Worker {hit_id}] Direct Fail (Bad Proxy): {e}")
            
        await context.close()
        
    except Exception as e:
        log(f"❌ [Worker {hit_id}] Context Error: {e}")

# --- TASK B: Web Proxy Hit (Using Croxy/Blockaway) ---
async def task_web_hit(browser, hit_id):
    target_link = get_fresh_token()
    if not target_link: return

    # Web Proxy List se uthao
    web_proxy_url = random.choice(WEB_PROXY_SITES)
    log(f"🛡️ [Worker {hit_id}] WEB HIT via {web_proxy_url}")
    
    # Isme Context ki zaroorat nahi, normal page chalega
    # (Lekin concurrency ke liye naya page hi chahiye)
    try:
        page = await browser.new_page()
        await page.goto(web_proxy_url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        
        # Input Logic
        input_found = False
        selectors = ["#url", "#request", "input[name='url']", "input[name='u']", "#web_proxy_url"]
        
        for selector in selectors:
            if await page.locator(selector).count() > 0:
                await page.locator(selector).fill(target_link)
                input_found = True
                break
        
        if input_found:
            await page.keyboard.press("Enter")
            await asyncio.sleep(10) # Redirect wait
            
            log(f"🛑 [Worker {hit_id}] Web Hit Loaded! Holding 20s...")
            await asyncio.sleep(20)
            log(f"✅ [Worker {hit_id}] Web Success!")
        else:
            log(f"⚠️ [Worker {hit_id}] Input not found on {web_proxy_url}")
            
        await page.close()
    except Exception as e:
        log(f"❌ [Worker {hit_id}] Web Fail: {e}")

# --- ORCHESTRATOR (Manager) ---
async def run_hybrid_mode():
    log("\n--- 🔥 HYBRID MODE STARTED ---")
    
    # Step 0: Proxies reload karo
    fetch_geonode_proxies()
    
    log("⏳ 60 Seconds Break (System Cool-down)...")
    await asyncio.sleep(60)
    
    log("🖥️ Launching Browser...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            
            # --- TASKS KA JADU ---
            # 1 Direct Hit + 2 Web Hits = Total 3
            tasks = [
                task_direct_hit(browser, "A-Direct"), # Task 1
                task_web_hit(browser, "B-Web"),       # Task 2
                task_web_hit(browser, "C-Web")        # Task 3
            ]
            
            log("🚀 Launching 1 Direct + 2 Web Attacks...")
            await asyncio.gather(*tasks)
            
            log("🏁 Batch Complete!")
            await browser.close()
            
    except Exception as e:
        log(f"❌ Critical Error: {e}")

# Wrapper Loop
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            loop.run_until_complete(run_hybrid_mode())
        except Exception as e:
            log(f"❌ Loop Error: {e}")
        log("💤 10s Rest...")
        time.sleep(10)

# --- SERVER ---
@app.route('/')
def home():
    return "Hybrid Bot Active! (1 Direct + 2 Web) 🚜"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

