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

# 🚜 TUMHARE LINKS (Jitne marzi daalo, par 3-4 hi rakhna load ke liye)
TARGET_LINKS = [
    "https://shortxlinks.com/Q0gNBbrR",  
    "https://shortxlinks.in/FhIBy",
    "https://shortxlinks.com/s157"
]

# --- SCOREBOARD (Stats) ---
STATS = {
    "total_cycles": 0,
    "success": 0,
    "fail": 0
}

# --- 🌍 THE ELITE LIST (Proxy Family) ---
MASTER_PROXY_LIST = [
    "https://www.blockaway.net",
    "https://www.croxyproxy.com",
    "https://www.croxyproxy.rocks",
    "https://www.croxy.net",
    "https://www.croxy.org",
    "https://www.croxyproxy.net",
    "https://www.hiload.org",
    "https://www.youtubeunblocked.live",
    "https://www.video-proxy.net"
]

ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
random.shuffle(ACTIVE_PROXY_LIST)

# --- HELPER: LOGGING ---
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

# --- PART 1: Token Logic (Sudhara hua) ---
def get_final_link(base_url, link_id):
    try:
        log(f"[{link_id}] 🔍 Token dhoondh raha hoon...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        r1 = requests.get(base_url, headers=headers, allow_redirects=False)
        
        if "location" not in r1.headers: 
            log(f"[{link_id}] ❌ Redirect location nahi mili.")
            return None
            
        meverge_url = r1.headers["location"]
        
        # Token Parsing
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        
        if "adlinkfly" in query:
            adlink_data = query["adlinkfly"][0]
            # Yahan assume kar rahe hain ki pattern wahi hai
            if "?" in adlink_data:
                token = adlink_data.split("?")[1] 
                final = f"https://shortxlinks.com/Q0gNBbrR?{token}"
                
                # YEH RAHA FINAL LINK PRINT
                log(f"[{link_id}] 🎯 FINAL LINK BANA: {final}")
                return final
            else:
                log(f"[{link_id}] ❌ Token format match nahi hua.")
                return None
        else:
            log(f"[{link_id}] ❌ 'adlinkfly' key nahi mili.")
            return None
            
    except Exception as e:
        log(f"[{link_id}] ❌ Token Error: {e}")
        return None

# --- PART 2: Bot Logic (With 1 Minute Wait) ---
async def process_one_link(link_id, url):
    global ACTIVE_PROXY_LIST, STATS
    
    if len(ACTIVE_PROXY_LIST) == 0:
        ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
        random.shuffle(ACTIVE_PROXY_LIST)

    # 1. Token nikalo
    target_link = get_final_link(url, link_id)
    
    if not target_link:
        STATS["fail"] += 1
        return

    # 2. THE BIG WAIT (1 Minute)
    log(f"[{link_id}] ☕ Token mil gaya. Ab 60 Seconds ka 'Chai-Sutta' break...")
    await asyncio.sleep(60)
    log(f"[{link_id}] 🏃‍♂️ Break khatam! Browser start kar raha hoon.")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = await browser.new_page()
            
            current_proxy = random.choice(ACTIVE_PROXY_LIST)
            log(f"[{link_id}] 🚀 Proxy: {current_proxy}")
            
            try:
                await page.goto(current_proxy, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                
                input_found = False
                selectors = ["#url", "#request", "input[name='url']", "#web_proxy_url", ".form-control"]
                
                for selector in selectors:
                    if await page.locator(selector).count() > 0:
                        await page.locator(selector).fill("") 
                        await page.fill(selector, target_link)
                        input_found = True
                        break
                
                if input_found:
                    await page.keyboard.press("Enter")
                    
                    # Redirect Wait
                    await asyncio.sleep(15)
                    new_title = await page.title()
                    log(f"[{link_id}] ✅ PASS! Title: {new_title}")
                    
                    STATS["success"] += 1
                    
                    # Connection Hold
                    log(f"[{link_id}] 🛑 Holding 20s...")
                    await asyncio.sleep(20)
                else:
                    log(f"[{link_id}] ⚠️ Input box nahi mila.")
                    STATS["fail"] += 1
                    
            except Exception as e:
                log(f"[{link_id}] ❌ Proxy/Page Error: {e}")
                STATS["fail"] += 1
            
            await browser.close()

    except Exception as e:
        log(f"[{link_id}] ❌ Browser Crash: {e}")
        STATS["fail"] += 1

# --- PART 3: Batch Manager ---
async def run_batch_cycle():
    STATS["total_cycles"] += 1
    log(f"\n--- 🎬 CYCLE #{STATS['total_cycles']} START ---")
    
    tasks = []
    for index, link in enumerate(TARGET_LINKS):
        task = process_one_link(f"Link-{index+1}", link)
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # --- CYCLE STATS ---
    log("\n--------------------------------")
    log(f"📊 SCOREBOARD (Cycle #{STATS['total_cycles']})")
    log(f"✅ PASS: {STATS['success']}")
    log(f"❌ FAIL: {STATS['fail']}")
    log("--------------------------------\n")

# Wrapper
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            loop.run_until_complete(run_batch_cycle())
        except Exception as e:
            log(f"❌ Loop Error: {e}")
        
        log("💤 30 Seconds Rest...")
        time.sleep(30)

# --- PART 4: Server with Stats ---
@app.route('/')
def home():
    # Web page pe bhi stats dikhenge
    return f"""
    <h1>🤖 Sugam's Elite Bot</h1>
    <p><b>Total Cycles:</b> {STATS['total_cycles']}</p>
    <p style="color:green;"><b>✅ Success:</b> {STATS['success']}</p>
    <p style="color:red;"><b>❌ Failed:</b> {STATS['fail']}</p>
    <p><i>Bot is running with 1-minute wait logic.</i></p>
    """

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

