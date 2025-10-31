#!/usr/bin/env python3
"""
Local Instagram Login Script
Run this locally to authenticate with Instagram in a visible browser.
The session will be saved and can be used by the deployed service.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright


async def login_instagram():
    """Open Instagram in a visible browser for you to log in"""
    # Use local data directory
    data_dir = Path(__file__).parent / "data"
    user_data_dir = data_dir / "user_data_dir"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    print("🌐 Opening Instagram in browser...")
    print("📝 Please log in to Instagram in the browser window that opens")
    print("💾 Your login session will be saved for the monitor to use")
    print("")
    
    async with async_playwright() as p:
        # Launch browser in NON-HEADLESS mode (visible)
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,  # VISIBLE browser!
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
        )
        
        # Open Instagram login page
        page = await browser.new_page()
        print("📍 Navigating to Instagram login...")
        await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        
        print("✅ Browser window opened!")
        print("")
        print("👤 Please log in to Instagram in the browser window")
        print("⏳ Waiting for you to complete login...")
        print("")
        
        # Wait for login - check if we're still on login page
        max_wait = 600  # 10 minutes
        check_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            current_url = page.url.lower()
            is_login_page = "login" in current_url or "accounts/login" in current_url
            
            # Check if logged in by looking for Instagram main page elements
            try:
                # Try to find elements that indicate we're logged in
                await page.wait_for_selector("[role='main']", timeout=1000)
                if not is_login_page:
                    print("")
                    print("✅ Login successful! You're logged in.")
                    print(f"📍 Current page: {page.url}")
                    break
            except:
                pass
            
            # Still on login page, keep waiting
            if elapsed % 30 == 0:  # Every 30 seconds
                print(f"⏳ Still waiting... ({elapsed // 60}m {elapsed % 60}s elapsed)")
            
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        
        if elapsed >= max_wait:
            print("")
            print("⏱️  Timeout reached. Assuming login complete or manual exit.")
        
        print("")
        print("💾 Session saved to:", user_data_dir)
        print("")
        print("📦 To use this session on Render:")
        print("   1. The session is saved in: ./data/user_data_dir")
        print("   2. You can copy this folder to Render's persistent disk")
        print("   3. Or run the monitor locally with this session")
        print("")
        print("🔄 To log out, delete the session folder and run this script again")
        print("")
        
        # Keep browser open for a bit so user can see it
        print("👀 Browser will close in 10 seconds... (press Ctrl+C to keep open)")
        try:
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("")
            print("🔓 Keeping browser open. Close it manually when done.")
            await asyncio.sleep(3600)  # Keep open for 1 hour
        finally:
            await browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Instagram Login Helper")
    print("=" * 60)
    print("")
    asyncio.run(login_instagram())

