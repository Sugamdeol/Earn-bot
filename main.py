
import requests
import asyncio
import random  # Random proxy choose karne ke liye
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
DEFAULT_URL = "https://shortxlinks.com/Q0gNBbrR"

# --- PROXY LIST (Tractor ke naye khet) ---
# Alag-alag proxy sites taaki block na ho
PROXY_SITES = [
    "https://www.croxyproxy.com",
    "https://www.croxyproxy.rocks",
    "https://www.blockaway.net",
    "https://www.proxysite.com",
    "https://www.hidemyass.com/en-in/proxy"
]

# --- PART 1: Token Nikalna ---
def get_final_link():
    try:
        print("🔍 Token dhoondh raha hoon...")
        r1 = requests.get(DEFAULT_URL, allow_redirects=False)
        if "location" not in r1.headers: return None
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        return f"https://shortxlinks.com/Q0gNBbrR?{token}"
    except Exception as e:
        print(f"❌ Token Error: {e}")
        return None

# --- PART 2: Async Playwright Logic ---
async def run_cycle():
    print("\n--- 🎬 New Cycle Start ---")
    
    # 1. Link Generate
    target_link = get_final_link()
    if not target_link:
        print("Link nahi bana. Skip.")
        return

    print(f"🔗 Target Link: {target_link}")
    
    # 2. Link Pakne ka time (Waise ka waisa)
    print("⏳ 1 Minute ka break (Link pakne do)...")
    await asyncio.sleep(60) 
    
    # 3. Browser Start
    print("\n🖥️ Playwright Browser start kar raha hoon...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # --- CHANGE: Random Proxy Pick ---
            current_proxy = random.choice(PROXY_SITES)
            print(f"🚀 Opening Proxy Website: {current_proxy}")
            
            try:
                await page.goto(current_proxy, timeout=60000)
                await page.wait_for_load_state("networkidle")
                print("✅ Proxy Site Open ho gayi!")
            except:
                print("⚠️ Site load nahi hui, agle cycle mein try karenge.")
                await browser.close()
                return

            # --- SMART INPUT FINDER ---
            # Hum tractor ko sikhayenge ki input box kahan-kahan ho sakta hai
            # Common IDs: #url, #request, input[name='u'], input[name='d']
            input_found = False
            possible_selectors = ["#url", "#request", "input[name='u']", "input[name='d']", "input[name='q']", "#input-url"]
            
            for selector in possible_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"🎯 Input box mil gaya: {selector}")
                    await page.fill(selector, target_link)
                    input_found = True
                    break
            
            if not input_found:
                print("⚠️ Input box nahi mila! (Format alag hai?)")
                await browser.close()
                return
            
            print("➡️ Link daal diya, Enter daba raha hoon...")
            await page.keyboard.press("Enter")
            
            # --- CHANGE: Step 6 (Wait 20 Seconds) ---
            print("🛑 Ab 20 Second hold karenge (Loading ke baad)...")
            
            # 4 baar x 5 sec = 20 Seconds
            for i in range(4, 0, -1):
                await asyncio.sleep(5)
                try:
                    title = await page.title()
                    print(f"   ⏳ Running... ({i*5}s remaining) Title: {title}")
                except:
                    print(f"   ⏳ Running... ({i*5}s remaining)")
            
            print("\n🏁 Mission Complete (20s Over)!")
            await browser.close()
            print("🔒 Browser Band.")
            
    except Exception as e:
        print(f"❌ Playwright Error: {e}")

# --- MAIN LOOP ---
async def main_loop():
    print("🚜 Smart Tractor (Multi-Khet Mode) Start! 🌾")
    try:
        while True:
            await run_cycle()
            print("\n💤 10 Second Rest (Cycle ke beech)...")
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("Stopped.")
    except Exception as e:
        print(f"Error in Loop: {e}")

# Colab Start Command:
await main_loop()
