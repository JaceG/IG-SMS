# Quick Guide: Twilio Steps 2 & 3

## Step 2: Buy/Verify a Twilio Number

### Get Your Credentials First

1. **Log into Twilio Console**: https://console.twilio.com
2. **Get Account SID & Auth Token**:
   - Click your account name (top right) → "Account Info"
   - Copy **Account SID** → This is `TWILIO_ACCOUNT_SID`
   - Click "Show" next to Auth Token → Copy → This is `TWILIO_AUTH_TOKEN`
   - ⚠️ **Keep these secret!** Add them to Render environment variables later.

### Buy a Phone Number

1. **Navigate to Phone Numbers**:
   - Click "Phone Numbers" in left sidebar
   - Click "Manage" → "Buy a number"
2. **Select & Purchase**:
   - Choose country (United States recommended)
   - Make sure **SMS** capability is checked ✅
   - Click "Search" → Choose any available number
   - Click "Buy" → Confirm ($1/month)
3. **Copy Your Number**:
   - After purchase, you'll see it in "Active numbers"
   - Copy the full number (format: `+1234567890`)
   - This is your `TWILIO_FROM_NUMBER`

**Save this number** - you'll need it for Step 3 and Render environment variables.

---

## Step 3: Configure Twilio Webhook

**Prerequisite**: Your Render service must be deployed and running first!

### Get Your Render URL

1. Go to Render Dashboard: https://dashboard.render.com
2. Open your `ig-sms` service
3. Copy your service URL (format: `https://ig-sms-xxxx.onrender.com`)
4. Your webhook URL will be: `https://ig-sms-xxxx.onrender.com/twilio/sms`

### Configure Webhook in Twilio

Follow [Twilio's official documentation](https://www.twilio.com/docs/usage/webhooks/getting-started-twilio-webhooks) for configuring incoming message webhooks:

#### Method 1: Phone Number (Recommended - Most Common)

1. **In Twilio Console**:
   - Go to https://www.twilio.com/console
   - Click **"Phone Numbers"** in left sidebar
   - Click **"Manage Numbers"** (or you may see "Manage" → "Active numbers")
   - Click on the phone number you purchased

2. **Set Messaging Webhook**:
   - Scroll down to the **"Messaging"** section
   - Find the field labeled **"A MESSAGE COMES IN"**
   - Select **"Webhook"** from the dropdown (or enter URL directly if it's a text field)
   - Enter your Render URL: `https://your-service-name.onrender.com/twilio/sms`
     - Replace `your-service-name` with your actual Render service name
     - **Must use `https://`** (Twilio requires HTTPS)
     - No trailing slash after `/twilio/sms`
   - Set **HTTP Method** to **POST**
   - Click **"Save"** (usually at bottom of page)

#### Method 2: Messaging Service (If Using One)

If you're using a Messaging Service:

1. **In Twilio Console**:
   - Go to **"Messaging"** → **"Services"** (or "SMS Notifications" → select your service)
   - Click on your Messaging Service
   - Click the **"Inbound"** tab

2. **Set Inbound Webhook**:
   - In "Incoming messages" section, select **"Send a webhook"** radio button
   - Enter your Render URL: `https://your-service-name.onrender.com/twilio/sms`
   - Ensure HTTP Method is **POST**
   - Click **"Save"** or **"Update"**

### Verify It Works

1. After saving, Twilio will automatically test the webhook
2. You should see: ✅ "Request successful" or similar
3. If it fails:
   - Check Render service is running: Visit `https://your-service.onrender.com/healthz`
   - Verify URL is exactly: `https://...onrender.com/twilio/sms` (no trailing slash)
   - Make sure you used `https://` not `http://`

---

## Visual Guide

```
Twilio Console → Phone Numbers → [Your Number] → Messaging Configuration
                                                              ↓
                    A MESSAGE COMES IN
                         ↓
                    [Webhook] ← Select this
                         ↓
    https://ig-sms-xxxxx.onrender.com/twilio/sms  ← Paste your Render URL
                         ↓
                    [POST] ← HTTP Method
                         ↓
                    [Save] ← Click to save
```

---

## Troubleshooting

**Webhook test fails:**
- ✅ Render service deployed? Check: `https://your-service.onrender.com/healthz`
- ✅ URL ends with `/twilio/sms`? (no trailing slash)
- ✅ Using `https://`? (required by Twilio)
- ✅ Render service is "Live" (not "Stopped")?

**Can't send SMS to your phone:**
- Trial accounts: Verify your phone number in Twilio Console → "Verified Caller IDs"
- Add your phone number there and verify via SMS or call

---

## Next Steps

After completing Steps 2 & 3:
1. Add Twilio credentials to Render environment variables (see SETUP_GUIDE.md Step 4)
2. Test by sending `STATUS IG` to your Twilio number

