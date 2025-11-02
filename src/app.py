import asyncio
import logging
import sys
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, Query, Form
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, Response
from ig_monitor.config import get_settings
from ig_monitor.sms import send_sms, validate_twilio_request
from ig_monitor.state import init_state
from ig_monitor.monitor import start_monitor, stop_monitor, is_monitor_running, get_browser_page

# Configure logging to output to stdout (so Render captures it)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="IG-SMS")
settings = get_settings()


@app.on_event("startup")
async def _startup() -> None:
    await init_state()


@app.get("/healthz")
async def healthz():
    return JSONResponse({
        "status": "ok",
        "poll_seconds": settings.poll_seconds,
        "data_dir": settings.data_dir,
        "monitor_running": is_monitor_running(),
    })


@app.post("/twilio/sms")
async def twilio_sms(request: Request):
    # Signature validation is optional (controlled by VALIDATE_TWILIO_SIGNATURE env var)
    await validate_twilio_request(request)

    form = await request.form()
    from_number = str(form.get("From", ""))
    body = str(form.get("Body", "")).strip()
    
    logger.info(f"Received SMS from {from_number}: {body}")
    logger.info(f"OWNER_PHONE in config: {settings.owner_phone}")

    # Normalize phone numbers for comparison (remove + and spaces, keep last 10 digits)
    def normalize_phone(phone: str) -> str:
        cleaned = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        return cleaned[-10:] if len(cleaned) >= 10 else cleaned
    
    from_normalized = normalize_phone(from_number)
    owner_normalized = normalize_phone(settings.owner_phone) if settings.owner_phone else ""
    
    logger.info(f"Comparing: from={from_normalized} vs owner={owner_normalized}")
    
    # Only accept commands from the owner
    if settings.owner_phone and from_normalized == owner_normalized:
        cmd = body.upper()
        logger.info(f"Command matched owner, processing: {cmd}")
        
        try:
            if "START IG" in cmd:
                status = await start_monitor()
                send_sms(settings.owner_phone, f"IG monitor {status}")
                logger.info(f"Sent START response: {status}")
                return PlainTextResponse("OK")
            if "STOP IG" in cmd:
                status = await stop_monitor()
                send_sms(settings.owner_phone, f"IG monitor {status}")
                logger.info(f"Sent STOP response: {status}")
                return PlainTextResponse("OK")
            if "STATUS IG" in cmd:
                running = is_monitor_running()
                send_sms(settings.owner_phone, f"IG monitor running: {running}")
                logger.info(f"Sent STATUS response: {running}")
                return PlainTextResponse("OK")
            # Fallback echo
            send_sms(settings.owner_phone, f"Received: {body}")
            logger.info(f"Sent echo response")
            return PlainTextResponse("OK")
        except Exception as e:
            logger.error(f"Error sending SMS: {e}", exc_info=True)
            return PlainTextResponse(f"ERROR: {str(e)}", status_code=500)

    logger.warning(f"Phone number mismatch - ignoring message from {from_number}")
    return PlainTextResponse("IGNORED", status_code=202)


def _check_token(token: Optional[str]) -> None:
    """Verify access token for browser interface"""
    if settings.app_secret_token:
        if not token or token != settings.app_secret_token:
            raise HTTPException(status_code=403, detail="Invalid token. Set token=YOUR_SECRET_TOKEN in URL")


@app.get("/browser")
async def browser_interface(token: str = Query(None)):
    """Remote browser interface - interact with Instagram browser session"""
    _check_token(token)
    
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>IG-SMS Remote Browser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; }
        h1 { margin-bottom: 20px; color: #333; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        button:hover { background: #0056b3; }
        button.secondary { background: #6c757d; }
        button.secondary:hover { background: #545b62; }
        button.danger { background: #dc3545; }
        button.danger:hover { background: #c82333; }
        input[type="text"], input[type="url"] { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; flex: 1; min-width: 200px; }
        .url-bar { display: flex; gap: 10px; margin-bottom: 20px; }
        .status { padding: 10px; background: #e9ecef; border-radius: 4px; margin-bottom: 20px; font-family: monospace; font-size: 12px; }
        #screenshot { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; cursor: crosshair; display: block; margin: 0 auto; }
        .screenshot-container { position: relative; margin-bottom: 20px; text-align: center; background: #f8f9fa; padding: 20px; border-radius: 4px; }
        .click-instructions { margin-top: 10px; color: #666; font-size: 12px; }
        .info-box { background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; padding: 15px; margin-bottom: 20px; }
        .info-box strong { color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 Remote Instagram Browser</h1>
        
        <div class="info-box">
            <strong>How to use:</strong>
            <ol style="margin-left: 20px; margin-top: 10px;">
                <li>Click "Open Instagram" to navigate to Instagram login</li>
                <li>The screenshot below shows what the browser sees</li>
                <li>Click anywhere on the screenshot to interact with the page</li>
                <li>Use "Type Text" to enter your username/password</li>
                <li>Once logged in, you can start the monitor via SMS: "START IG"</li>
            </ol>
        </div>
        
        <div class="controls">
            <button onclick="navigateTo('https://www.instagram.com/accounts/login/')">📱 Open Instagram Login</button>
            <button onclick="navigateTo('https://www.instagram.com/')">🏠 Go to Instagram Home</button>
            <button onclick="getScreenshot()" class="secondary">🔄 Refresh Screenshot</button>
            <button onclick="checkLoginStatus()" class="secondary">✅ Check Login Status</button>
            <button onclick="goToThread()">💬 Go to DM Thread</button>
        </div>
        
        <div class="url-bar">
            <input type="url" id="urlInput" placeholder="Enter URL to navigate to..." />
            <button onclick="navigateFromInput()">Go</button>
        </div>
        
        <div class="status" id="status">Ready. Click "Open Instagram Login" to start.</div>
        
        <div class="screenshot-container">
            <img id="screenshot" onclick="handleScreenshotClick(event)" />
            <div class="click-instructions">Click on the image above to interact with the page</div>
        </div>
        
        <div class="controls">
            <input type="text" id="typeInput" placeholder="Type text to send to focused element..." />
            <button onclick="typeText()">⌨️ Type Text</button>
            <button onclick="pressEnter()">⏎ Press Enter</button>
            <button onclick="pressTab()">⇥ Press Tab</button>
        </div>
    </div>
    
    <script>
        const token = new URLSearchParams(window.location.search).get('token') || '';
        
        function updateStatus(msg, isError = false) {
            const status = document.getElementById('status');
            status.textContent = msg;
            status.style.background = isError ? '#f8d7da' : '#e9ecef';
            status.style.color = isError ? '#721c24' : '#333';
        }
        
        async function navigateTo(url) {
            updateStatus(`Navigating to ${url}...`);
            try {
                const response = await fetch(`/browser/navigate?token=${token}&url=${encodeURIComponent(url)}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Navigation failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.success) {
                    updateStatus(`✅ Navigated to ${url}`);
                    setTimeout(getScreenshot, 1000);
                    setTimeout(checkLoginStatus, 2000);
                } else {
                    updateStatus(`❌ Error: ${data.error || 'Failed to navigate'}`, true);
                }
            } catch (e) {
                updateStatus(`❌ Error: ${e.message}`, true);
            }
        }
        
        async function navigateFromInput() {
            const url = document.getElementById('urlInput').value.trim();
            if (url) {
                if (!url.startsWith('http://') && !url.startsWith('https://')) {
                    navigateTo('https://' + url);
                } else {
                    navigateTo(url);
                }
            }
        }
        
        async function getScreenshot() {
            const img = document.getElementById('screenshot');
            let retryCount = 0;
            const maxRetries = 3;
            
            const loadImage = () => {
                const timestamp = Date.now();
                const imgSrc = `/browser/screenshot?token=${token}&t=${timestamp}`;
                
                img.onerror = function() {
                    retryCount++;
                    if (retryCount < maxRetries) {
                        updateStatus(`⏳ Screenshot loading... (retry ${retryCount}/${maxRetries})`);
                        setTimeout(() => loadImage(), 2000);
                    } else {
                        updateStatus('❌ Failed to load screenshot. Browser may not be initialized yet. Try clicking "Open Instagram Login" first.', true);
                        img.style.display = 'none';
                    }
                };
                
                img.onload = function() {
                    // Check if image is the 1x1 transparent PNG (error case)
                    if (img.naturalWidth === 1 && img.naturalHeight === 1) {
                        retryCount++;
                        if (retryCount < maxRetries) {
                            updateStatus(`⏳ Browser initializing... (retry ${retryCount}/${maxRetries})`);
                            setTimeout(() => loadImage(), 2000);
                        } else {
                            updateStatus('❌ Browser not ready. Try clicking "Open Instagram Login" to initialize the browser.', true);
                            img.style.display = 'none';
                        }
                    } else {
                        updateStatus('✅ Screenshot loaded');
                        img.style.display = 'block';
                        retryCount = 0; // Reset on success
                    }
                };
                
                updateStatus('📸 Loading screenshot...');
                img.src = imgSrc;
            };
            
            loadImage();
        }
        
        async function checkLoginStatus() {
            try {
                const response = await fetch(`/browser/status?token=${token}`);
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Status check failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.logged_in) {
                    updateStatus('✅ Logged in to Instagram! You can now use the monitor.');
                } else {
                    updateStatus('⏳ Not logged in. Please complete login in the browser.');
                }
            } catch (e) {
                updateStatus(`❌ Error checking status: ${e.message}`, true);
            }
        }
        
        async function handleScreenshotClick(event) {
            const img = event.target;
            if (!img.naturalWidth || !img.naturalHeight) {
                updateStatus('⏳ Screenshot not loaded yet, please wait...', true);
                return;
            }
            const rect = img.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Scale coordinates based on actual image size vs displayed size
            const scaleX = img.naturalWidth / rect.width;
            const scaleY = img.naturalHeight / rect.height;
            const actualX = Math.round(x * scaleX);
            const actualY = Math.round(y * scaleY);
            
            updateStatus(`Clicking at (${actualX}, ${actualY})...`);
            try {
                const response = await fetch(`/browser/click?token=${token}&x=${actualX}&y=${actualY}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Click failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.success) {
                    updateStatus(`✅ Clicked at (${actualX}, ${actualY})`);
                    setTimeout(getScreenshot, 500);
                } else {
                    updateStatus(`❌ Click failed: ${data.error || 'Unknown error'}`, true);
                }
            } catch (e) {
                updateStatus(`❌ Error: ${e.message}`, true);
            }
        }
        
        async function typeText() {
            const text = document.getElementById('typeInput').value;
            if (!text) return;
            
            updateStatus(`Typing text...`);
            try {
                const response = await fetch(`/browser/type?token=${token}&text=${encodeURIComponent(text)}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Type failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.success) {
                    updateStatus(`✅ Typed text`);
                    document.getElementById('typeInput').value = '';
                    setTimeout(getScreenshot, 300);
                } else {
                    updateStatus(`❌ Type failed: ${data.error || 'Unknown error'}`, true);
                }
            } catch (e) {
                updateStatus(`❌ Error: ${e.message}`, true);
            }
        }
        
        async function pressEnter() {
            await sendKey('Enter');
        }
        
        async function pressTab() {
            await sendKey('Tab');
        }
        
        async function sendKey(key) {
            try {
                const response = await fetch(`/browser/key?token=${token}&key=${key}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Key press failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.success) {
                    setTimeout(getScreenshot, 300);
                }
            } catch (e) {
                updateStatus(`❌ Error: ${e.message}`, true);
            }
        }
        
        async function goToThread() {
            updateStatus('Navigating to DM thread...');
            try {
                const response = await fetch(`/browser/thread?token=${token}`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const text = await response.text();
                    updateStatus(`❌ Thread navigation failed: ${response.status} ${text}`, true);
                    return;
                }
                const data = await response.json();
                if (data.success) {
                    updateStatus('✅ Opened DM thread');
                    setTimeout(getScreenshot, 1000);
                } else {
                    updateStatus(`❌ Error: ${data.error || 'Failed'}`, true);
                }
            } catch (e) {
                updateStatus(`❌ Error: ${e.message}`, true);
            }
        }
        
        // Auto-refresh screenshot every 5 seconds
        setInterval(getScreenshot, 5000);
        
        // Initial load
        getScreenshot();
        checkLoginStatus();
        
        // Allow Enter key in URL input
        document.getElementById('urlInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') navigateFromInput();
        });
        
        // Allow Enter key in type input
        document.getElementById('typeInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') typeText();
        });
    </script>
</body>
</html>
    """)


# Lock to prevent concurrent navigations
_navigation_lock = asyncio.Lock()

@app.get("/browser/screenshot")
async def browser_screenshot(token: str = Query(None)):
    """Get screenshot of current browser state"""
    _check_token(token)
    try:
        # Add timeout for entire operation (20 seconds max - reduced from 30)
        async def _take_screenshot():
            page = await get_browser_page()
            
            # Only navigate if page is truly blank, and use lock to prevent conflicts
            # Skip navigation if it's likely to fail or conflict
            current_url = page.url
            if current_url and current_url not in ["about:blank", ""] and "about:" not in current_url:
                # Page has content, just screenshot it
                pass
            else:
                # Page is blank - try to navigate but don't block on it
                # Use lock to prevent multiple simultaneous navigations
                async with _navigation_lock:
                    try:
                        # Quick check if still blank (might have been navigated by another request)
                        if page.url in ["about:blank", ""] or "about:" in page.url:
                            logger.info("Page is blank, attempting navigation...")
                            # Use shorter timeout and don't wait for full load
                            await asyncio.wait_for(
                                page.goto("https://www.instagram.com", wait_until="domcontentloaded", timeout=5000),
                                timeout=6.0
                            )
                            # Give it a moment to render
                            await asyncio.sleep(1)
                    except (asyncio.TimeoutError, Exception) as nav_error:
                        logger.warning(f"Navigation skipped or failed: {type(nav_error).__name__}: {nav_error}")
                        # Continue to screenshot anyway - might be a blank/loading page
            
            # Try to screenshot whatever is there - even if blank or loading
            try:
                screenshot_bytes = await asyncio.wait_for(
                    page.screenshot(full_page=False, clip={"x": 0, "y": 0, "width": 800, "height": 600}),
                    timeout=5.0  # Reduced timeout for screenshot itself
                )
                return Response(content=screenshot_bytes, media_type="image/png")
            except Exception as screenshot_error:
                logger.warning(f"Screenshot capture failed: {screenshot_error}, trying without clip...")
                # Fallback: try screenshot without clip
                screenshot_bytes = await page.screenshot(full_page=False, timeout=5000)
                return Response(content=screenshot_bytes, media_type="image/png")
        
        return await asyncio.wait_for(_take_screenshot(), timeout=20.0)
    except asyncio.TimeoutError:
        logger.error("Screenshot operation timed out after 20 seconds")
        transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(content=transparent_png, media_type="image/png", status_code=504)  # 504 Gateway Timeout
    except Exception as e:
        logger.error(f"Screenshot error: {e}", exc_info=True)
        transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(content=transparent_png, media_type="image/png", status_code=500)


@app.get("/browser/status")
async def browser_status(token: str = Query(None)):
    """Check if logged into Instagram"""
    _check_token(token)
    try:
        from ig_monitor.monitor import is_logged_in
        page = await get_browser_page()
        logged_in = await is_logged_in(page)
        current_url = page.url
        return JSONResponse({"logged_in": logged_in, "url": current_url})
    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        return JSONResponse({"logged_in": False, "error": str(e)})


@app.post("/browser/navigate")
async def browser_navigate(url: str = Query(...), token: str = Query(None)):
    """Navigate browser to a URL"""
    _check_token(token)
    try:
        page = await get_browser_page()
        await page.goto(url, wait_until="networkidle")
        return JSONResponse({"success": True, "url": page.url})
    except Exception as e:
        logger.error(f"Navigate error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/browser/click")
async def browser_click(x: int = Query(...), y: int = Query(...), token: str = Query(None)):
    """Click at coordinates in the browser"""
    _check_token(token)
    try:
        page = await get_browser_page()
        await page.mouse.click(x, y)
        await page.wait_for_timeout(500)  # Wait for any navigation/updates
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Click error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/browser/type")
async def browser_type(text: str = Query(...), token: str = Query(None)):
    """Type text into the currently focused element"""
    _check_token(token)
    try:
        page = await get_browser_page()
        await page.keyboard.type(text, delay=50)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Type error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/browser/key")
async def browser_key(key: str = Query(...), token: str = Query(None)):
    """Press a key (Enter, Tab, etc.)"""
    _check_token(token)
    try:
        page = await get_browser_page()
        await page.keyboard.press(key)
        await page.wait_for_timeout(300)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Key press error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/browser/thread")
async def browser_thread(token: str = Query(None)):
    """Navigate to the configured DM thread"""
    _check_token(token)
    try:
        page = await get_browser_page()
        await page.goto(settings.ig_thread_url, wait_until="networkidle")
        return JSONResponse({"success": True, "url": page.url})
    except Exception as e:
        logger.error(f"Thread navigation error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


