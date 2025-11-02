# Browser Anti-Detection Guide

Instagram and other platforms detect automated browsers. This guide covers solutions from easiest to most robust.

## Current Improvements (Applied)

We've added several anti-detection measures:

1. **Stealth Plugin**: `playwright-stealth` package to hide automation signals
2. **Updated Chrome Flags**: Removed automation-detecting flags, added stealth flags
3. **Realistic User Agent**: Updated to Chrome 131 (latest)
4. **Realistic Viewport**: Changed from 800x600 to 1366x768 (common desktop size)
5. **HTTP Headers**: Added realistic browser headers
6. **JavaScript Overrides**: Hides `navigator.webdriver` and other automation signals

## If Detection Still Occurs

### Option 1: Use Real Browser Service (Recommended for Production)

**Browserbase** - Provides real Chrome browsers in the cloud that look like regular user browsers.

**Setup:**
1. Sign up at https://www.browserbase.com
2. Get API key
3. Install package: `pip install browserbase`
4. Modify `src/ig_monitor/monitor.py` to use Browserbase instead of Playwright

**Pros:**
- Real Chrome browsers (not headless)
- Hard to detect
- Handles browser management
- Can see what's happening in real-time

**Cons:**
- Paid service (~$0.01-0.05 per minute)
- Requires API changes

### Option 2: Use Residential Proxy

Some detection is based on IP address. Using a residential proxy can help:
- Services like Bright Data, Smartproxy, or Oxylabs
- Set proxy in Playwright: `proxy={"server": "http://proxy-url:port"}`

### Option 3: Use Playwright in Non-Headless Mode (Already Supported)

Set environment variable: `HEADLESS_BROWSER=false`

This runs with a visible browser window, which is slightly less detectable but won't work well on a server.

### Option 4: Use Undetected-Playwright (Alternative Stealth)

Try a different stealth package:
```bash
pip install undetected-playwright
```

### Option 5: Use Your Own Browser Session

1. Log into Instagram in your own browser first
2. Export cookies
3. Import cookies into Playwright session
4. This avoids the login detection entirely

## Testing Detection

You can test if you're being detected:
1. Go to: https://bot.sannysoft.com/
2. Or: https://arh.antoinevastel.com/bots/areyouheadless
3. Check for automation signals

## Best Practices

1. **Use persistent context** (already implemented) - Maintains session
2. **Don't rush actions** - Add delays between actions
3. **Use realistic timing** - Don't act too fast
4. **Stay logged in** - Avoid frequent logins
5. **Use same IP** - Residential proxies help
6. **Human-like behavior** - Random delays, mouse movements

## Current Status

With the stealth improvements, the browser should be much less detectable. Try logging in again after deploying. If Instagram still blocks, consider Browserbase for a more robust solution.

