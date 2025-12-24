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

# 🚜 YAHAN APNE SAARE LINKS DAALO
TARGET_LINKS = [
    "https://shortxlinks.com/Q0gNBbrR",  # Link 1
    "https://shortxlinks.com/s157",  # Link 2 (Demo ke liye same rakha hai, alag kar lena)
    "https://shortxlinks.in/FhIBy"   # Link 3
]

# --- 🌍 THE ELITE LIST (Sirf Blockaway Family) ---
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

# --- WORKING LIST ---
ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
random.shuffle(ACTIVE_PROXY_LIST)

# --- HELPER: LOGGING ---
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

# --- PART 1: Token Logic (Har link ke liye alag) ---
def get_final_link(base_url, link_id):
    try:
        log(f"[{link_id}] 🔍 Token dhoondh raha hoon...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        r1 = requests.get(base_url, headers=headers, allow_redirects=False)
        
        if "location" not in r1.headers: 
            return None
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        final = f"https://shortxlinks.com/Q0gNBbrR?{token}"
        log(f"[{link_id}] ✅ Token Mil Gaya!")
        return final
    except Exception as e:
        log(f"[{link_id}] ❌ Token Error: {e}")
        return None

# --- PART 2: Single Bot Logic (Ek sipahi ka kaam) ---
async def process_one_link(link_id, url):
    global ACTIVE_PROXY_LIST
    
    # Check agar list khali ho gayi
    if len(ACTIVE_PROXY_LIST) == 0:
        log(f"[{link_id}] ⚠️ Proxy khatam! List reload kar raha hoon.")
        ACTIVE_PROXY_LIST = MASTER_PROXY_LIST.copy()
        random.shuffle(ACTIVE_PROXY_LIST)

    # Token nikalo
    target_link = get_final_link(url, link_id)
    
    if not target_link:
        log(f"[{link_id}] ⚠️ Skip kar raha hoon (Token failed).")
        return

    # Random delay taaki saare browser bilkul ek second pe na khule (load bachega)
    start_delay = random.randint(1, 10)
    log(f"[{link_id}] ⏳ {start_delay}s ruk ke start karunga...")
    await asyncio.sleep(start_delay)

    try:
        async with async_playwright() as p:
            # Browser Launch
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = await browser.new_page()
            
            # Proxy pick karo (Randomly pick kar rahe hain taaki race condition na ho)
            current_proxy = random.choice(ACTIVE_PROXY_LIST)
            
            log(f"[{link_id}] 🚀 Using Proxy: {current_proxy}")
            
            try:
                await page.goto(current_proxy, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                
                # --- INPUT FINDER ---
                input_found = False
                selectors = ["#url", "#request", "input[name='url']", "#web_proxy_url", ".form-control"]
                
                for selector in selectors:
                    if await page.locator(selector).count() > 0:
                        await page.locator(selector).fill("") 
                        await page.fill(selector, target_link)
                        input_found = True
                        break
                
                if input_found:
                    log(f"[{link_id}] ➡️ Link daal diya, Go!")
                    await page.keyboard.press("Enter")
                    
                    # Wait for redirect
                    await asyncio.sleep(15)
                    new_title = await page.title()
                    log(f"[{link_id}] ✅ Success! Page Title: {new_title}")
                    
                    # Hold Connection
                    log(f"[{link_id}] 🛑 Holding 20s...")
                    await asyncio.sleep(20)
                else:
                    log(f"[{link_id}] ⚠️ Input box nahi mila.")
                    
            except Exception as e:
                log(f"[{link_id}] ❌ Error: {e}")
            
            await browser.close()
            log(f"[{link_id}] 🏁 Mission Complete.")

    except Exception as e:
        log(f"[{link_id}] ❌ Browser Crash: {e}")

# --- PART 3: The Manager (Sabko ek saath chalayega) ---
async def run_batch_cycle():
    log("\n--- 🎬 KA-BOOM! Starting Multi-Link Cycle ---")
    
    # Saare tasks banao
    tasks = []
    for index, link in enumerate(TARGET_LINKS):
        # Har task ko ek ID de rahe hain: Link-1, Link-2...
        task = process_one_link(f"Link-{index+1}", link)
        tasks.append(task)
    
    # Sabko ek saath run karo (Yeh hai asli magic!)
    await asyncio.gather(*tasks)
    
    log("\n--- ✅ Cycle Finished (Sabka kaam ho gaya) ---")

# Wrapper for Thread
def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    while True:
        try:
            loop.run_until_complete(run_batch_cycle())
        except Exception as e:
            log(f"❌ Loop Error: {e}")
            
        log("💤 30 Seconds Rest (Thoda saans le lo)...")
        time.sleep(30)

# --- PART 4: Server ---
@app.route('/')
def home():
    return f"Sugam's Multi-Bot is Running! Targets: {len(TARGET_LINKS)} 🚀"

if __name__ == "__main__":
    t = threading.Thread(target=start_background_loop)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
