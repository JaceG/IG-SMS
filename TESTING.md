# Testing Your Twilio Webhook Setup

## Step 1: Verify Your Render Service is Running

Before testing the webhook, make sure your Render service is deployed and running:

1. **Check Health Endpoint**:
   - Open in browser: `https://ig-sms.onrender.com/healthz`
   - Should return: `{"status":"ok","poll_seconds":90,"data_dir":"/data","monitor_running":false}`
   - If you get an error, your service isn't deployed or is down

2. **Check Render Dashboard**:
   - Go to https://dashboard.render.com
   - Open your `ig-sms` service
   - Verify status is **"Live"** (green) not "Stopped" or "Error"

## Step 2: Test with Twilio Console (Easiest)

Twilio can test your webhook directly:

1. **In Twilio Console**:
   - Go to your Messaging Service ("Sports Bet") or Phone Number
   - Navigate to the webhook configuration page
   - Look for a **"Test"** or **"Test Webhook"** button
   - Click it - Twilio will send a test request to your webhook

2. **Check the Result**:
   - Twilio should show "Request successful" or similar
   - If it fails, check:
     - Your Render URL is correct: `https://ig-sms.onrender.com/twilio/sms`
     - Your Render service is running (Step 1)
     - The URL uses `https://` not `http://`

## Step 3: Send a Test SMS (Recommended)

This is the most realistic test:

1. **From Your Phone**:
   - Send a text message to your Twilio number (`+18775842644` or whatever number you bought)
   - Try sending: `STATUS IG`

2. **Expected Behavior**:
   - You should receive a reply SMS within a few seconds: `"IG monitor running: False"`
   - If you don't receive a reply, the webhook isn't working correctly

3. **If You Get an Error Reply**:
   - The webhook is receiving messages but something is wrong with processing
   - Check Render logs (see Step 4)

## Step 4: Check Render Logs

1. **In Render Dashboard**:
   - Open your `ig-sms` service
   - Click the **"Logs"** tab
   - You should see log entries when:
     - A webhook is received
     - Any errors occur
     - The app processes a message

2. **What to Look For**:
   - ✅ **Success**: `INFO: POST /twilio/sms 200 OK` or similar
   - ❌ **Error**: Any error messages or stack traces
   - 🔍 **Incoming requests**: Logs showing POST requests to `/twilio/sms`

## Step 5: Check Twilio Logs

1. **In Twilio Console**:
   - Go to **"Monitor"** → **"Logs"** → **"Messaging"**
   - You'll see all incoming/outgoing messages
   - Look for your test message

2. **Check Webhook Status**:
   - Click on a message log entry
   - Look at "Webhook" section
   - Should show:
     - Status: `200 OK` (success) or an error code
     - URL: Your webhook URL
     - Response time

## Step 6: Manual curl Test (Advanced)

If signature validation is disabled (`VALIDATE_TWILIO_SIGNATURE=false`):

```bash
curl -X POST https://ig-sms.onrender.com/twilio/sms \
  -d "From=%2B1234567890" \
  -d "To=%2B18775842644" \
  -d "Body=STATUS IG"
```

**Expected Response**: `OK` or the actual response from your app

**Note**: This won't work if signature validation is enabled (default). Real Twilio requests include a signature that must be validated.

## Troubleshooting

### "Request failed" in Twilio Console
- ✅ Check Render service is running: Visit `https://ig-sms.onrender.com/healthz`
- ✅ Verify webhook URL is exactly: `https://ig-sms.onrender.com/twilio/sms`
- ✅ Check Render logs for errors

### SMS sent but no reply received
- ✅ Check `OWNER_PHONE` in Render matches your phone number (with country code, e.g., `+1234567890`)
- ✅ Check Twilio account isn't in trial mode (can only send to verified numbers)
- ✅ Verify your phone number in Twilio Console → "Verified Caller IDs"
- ✅ Check Render logs for processing errors

### Signature validation errors
- If you see "Invalid Twilio signature" or "Missing Twilio signature":
  - Option 1: Disable temporarily for testing: Set `VALIDATE_TWILIO_SIGNATURE=false` in Render
  - Option 2: Verify Twilio is sending the signature header (check Twilio logs)

### Service not responding
- Check Render service status
- Verify environment variables are set correctly
- Check Render logs for startup errors
- Try redeploying the service

## Quick Test Checklist

- [ ] Render service is "Live" and responds to `/healthz`
- [ ] Webhook URL in Twilio is: `https://ig-sms.onrender.com/twilio/sms`
- [ ] Sent test SMS to Twilio number
- [ ] Received reply SMS
- [ ] Render logs show incoming webhook requests
- [ ] Twilio logs show webhook status as `200 OK`

If all checkboxes pass, your webhook is set up correctly! ✅

