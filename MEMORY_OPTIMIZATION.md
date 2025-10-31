# Memory Optimization Guide

This app uses Playwright with Chromium, which can be memory-intensive. Here are the optimizations we've made and what to do if you're still running out of memory.

## Current Optimizations

1. **Chromium Memory Flags**: Added numerous flags to disable unnecessary features and limit memory usage
   - Disabled background processes, extensions, notifications, etc.
   - Set JavaScript heap size limit to 256MB
   - Disabled GPU and sandboxing (not needed for headless)

2. **Reduced Viewport Size**: Changed from 1280x900 to 800x600 to reduce memory footprint

3. **Limited Element Queries**: Reduced from checking 30 elements to 10 when extracting messages

4. **Periodic Garbage Collection**: Runs garbage collection periodically during monitoring

5. **Smaller Screenshots**: Screenshots are clipped to 800x600 instead of full page

## If Still Running Out of Memory

### Option 1: Upgrade Render Plan (Recommended)

The **Starter** plan has ~512MB RAM, which is tight for Playwright. Consider upgrading:

1. Go to your Render dashboard
2. Edit your service
3. Change plan from **Starter** to **Standard** (has 2GB RAM)
4. Redeploy

To change in `render.yaml`:
```yaml
plan: standard  # Instead of starter
```

### Option 2: Reduce Polling Frequency

Increase `POLL_SECONDS` environment variable to poll less frequently (e.g., 180 seconds instead of 90). This gives more time between checks for memory to be freed.

### Option 3: Stop Monitoring When Not Needed

Use `STOP IG` SMS command to stop monitoring when you don't need it. The browser stays logged in, but monitoring stops, freeing up memory.

### Option 4: Restart Service Periodically

You can manually restart the service from Render dashboard, or set up a scheduled restart.

## Monitoring Memory Usage

Check your Render service logs for memory warnings or OOM (Out of Memory) errors. Render will show memory usage in the service metrics.

## Additional Notes

- The browser session persists on disk, so restarting doesn't lose your login
- Memory usage is highest when:
  - Browser first starts
  - Taking screenshots
  - Navigating between pages
- Once monitoring is running and stable, memory usage should be more consistent

