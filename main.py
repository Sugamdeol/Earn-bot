import os
import time
import threading
import requests
from flask import Flask
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
app = Flask(__name__)
DEFAULT_URL = "https://shortxlinks.com/Q0gNBbrR"

# --- PART 1: Token Logic ---
def get_final_link():
    try:
        print("🔍 Token dhoondh raha hoon...")
        # Headers lagana zaroori hai server pe taaki bot na lage
        headers = {'User-Agent': 'Mozilla/5.0'}
        r1 = requests.get(DEFAULT_URL, headers=headers, allow_redirects=False)
        
        if "location" not in r1.headers: 
            print("❌ Redirect location nahi mili.")
            return None
            
        meverge_url = r1.headers["location"]
        
        parsed = urlparse(meverge_url)
        query = parse_qs(parsed.query)
        
        if "adlinkfly" not in query:
            print("❌ adlinkfly parameter nahi mila.")
            return None

        adlink_data = query["adlinkfly"][0]
        token = adlink_data.split("Q0gNBbrR?")[1]
        
        return f"https://shortxlinks.com/Q0gNBbrR?{token}"
    except Exception as e:
        print(f"❌ Token Error: {e}")
        return None

# --- PART 2: Bot Logic (Background Worker) ---
def run_bot_loop():
    print("🚜 Bot Engine Started in Background...")
    
    while True:
        print("\n--- 🎬 New Cycle Start ---")
        
        # 1. Link Generate
        target_link = get_final_link()
        
        if target_link:
            print(f"🔗 Target Link: {target_link}")
            
            # 2. Wait 1 Minute
            print("⏳ 1 Minute ka break...")
            time.sleep(60)
            
            # 3. Playwright Action
            try:
                with sync_playwright() as p:
                    # Render pe 'chromium' use karenge
                    # headless=True zaroori hai kyunki Render pe screen nahi hoti
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    print("🚀 Opening CroxyProxy...")
                    page.goto("https://www.croxyproxy.com", timeout=90000)
                    page.wait_for_load_state("networkidle")
                    
                    # Input logic
                    try:
                        if page.locator("#url").count() > 0:
                            page.fill("#url", target_link)
                        elif page.locator("#request").count() > 0:
                            page.fill("#request", target_link)
                        else:
                            print("⚠️ Input box nahi mila.")
                            browser.close()
                            continue
                        
                        print("➡️ Link daal diya, Go!")
                        page.keyboard.press("Enter")
                        
                        # 30 Second Hold
                        print("🛑 Holding for 30 seconds...")
                        time.sleep(30)
                        print("✅ Cycle Complete!")
                        
                    except Exception as e:
                        print(f"⚠️ Page Error: {e}")
                    
                    browser.close()
            except Exception as e:
                print(f"❌ Browser Crash: {e}")
        else:
            print("⚠️ Link fail, retrying in 10s...")
            time.sleep(10)

        print("💤 10 Second Rest...")
        time.sleep(10)

# --- PART 3: Web Server (To keep Render Alive) ---
@app.route('/')
def home():
    return "Sugam bhai ka Bot chal raha hai! 🚜"

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Bot ko alag thread (dhage) mein start karo
    # Taaki wo server ko block na kare
    t = threading.Thread(target=run_bot_loop)
    t.start()
    
    # Server start karo (Render PORT environment variable deta hai)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
