# Setup Guide: Twilio & Render Configuration

## Prerequisites
- GitHub repository pushed (already done ✅)
- Twilio account (create at https://www.twilio.com if needed)
- Render account (create at https://render.com if needed)

---

## Step 1: Deploy to Render (Get Your URL First)

### Option A: Using Render Dashboard (Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Connect GitHub**: 
   - Click "New +" → "Blueprint"
   - Authorize Render to access your GitHub if prompted
   - Select the `IG-SMS` repository
3. **Create Web Service**:
   - Render should detect `render.yaml` automatically
   - If not, select "New Web Service" → Connect your `IG-SMS` repo
   - Service name will be `ig-sms`
4. **Add Persistent Disk**:
   - In the service settings, go to "Disks"
   - Click "Add Disk"
   - Name: `data`
   - Mount Path: `/data`
   - Size: `2 GB`
5. **Set Environment Variables** (we'll fill these in step 2-3):
   - Go to "Environment" tab
   - Add these variables (we'll get values from Twilio next):
     ```
     DATA_DIR=/data
     TWILIO_ACCOUNT_SID=(from Twilio)
     TWILIO_AUTH_TOKEN=(from Twilio)
     TWILIO_FROM_NUMBER=(from Twilio - buy number first)
     OWNER_PHONE=(your phone, e.g., +1234567890)
     IG_THREAD_URL=(your Instagram DM thread URL)
     POLL_SECONDS=90
     ```
6. **Deploy**:
   - Click "Create Web Service" or "Save Changes"
   - Wait for deployment (takes 5-10 minutes first time)
   - **Copy your Render URL**: `https://ig-sms-xxxx.onrender.com` (you'll need this for Twilio webhook)

### Option B: Using Render CLI

If you have Render CLI installed:
```bash
render deploy
```

---

## Step 2: Buy/Verify a Twilio Number

1. **Log into Twilio**: https://console.twilio.com
2. **Navigate to Phone Numbers**:
   - Click "Phone Numbers" → "Manage" → "Buy a number"
3. **Buy a Number**:
   - Select your country (United States recommended)
   - For SMS capabilities, make sure "SMS" is checked
   - Click "Search" → Choose an available number → Click "Buy"
   - Confirm purchase (costs ~$1/month + $0.0085 per SMS)
4. **Copy Your Number**:
   - Once purchased, you'll see it in "Active numbers"
   - Copy the full number (format: +1234567890)
   - This is your `TWILIO_FROM_NUMBER`

5. **Get Your Credentials**:
   - In Twilio Console, go to "Account" → "Account Info" (or click your account name)
   - Copy:
     - **Account SID**: This is your `TWILIO_ACCOUNT_SID`
     - **Auth Token**: Click "Show" to reveal → This is your `TWILIO_AUTH_TOKEN`
     - ⚠️ Keep these secret!

---

## Step 3: Configure Twilio Webhook

Based on [Twilio's official documentation](https://www.twilio.com/docs/usage/webhooks/getting-started-twilio-webhooks), here's how to configure webhooks for incoming SMS messages:

### Configure via Phone Number (Recommended)

1. **In Twilio Console**:
   - Log in at https://www.twilio.com/console
   - Navigate to **"Phone Numbers"** in the left sidebar
   - Click **"Manage"** → **"Active numbers"** (or just click "Phone Numbers" if you see "Manage Numbers" directly)
   - Click on the phone number you purchased in Step 2

2. **Configure Messaging Webhook**:
   - Scroll down to the **"Messaging"** section
   - Find the field labeled **"A MESSAGE COMES IN"**
   - In the dropdown or input field, select **"Webhook"** or enter your webhook URL directly
   - Enter your Render URL: `https://your-service-name.onrender.com/twilio/sms`
     - Replace `your-service-name` with your actual Render service name
     - Example: `https://ig-sms-abc123.onrender.com/twilio/sms`
   - **Important**: 
     - Use `https://` (not `http://`) - Twilio requires HTTPS
     - The URL should end with `/twilio/sms` (no trailing slash)
   - Set **HTTP method** to **POST**
   - Click **"Save"** at the bottom of the page

### Alternative: Via Messaging Service

If you're using a Messaging Service (you'll see "Messaging Services" or "SMS Notifications" in the console):

1. **In Twilio Console**:
   - Navigate to **"Messaging"** → **"Services"** (or look for "SMS Notifications" in left sidebar)
   - Click on your Messaging Service
   - Go to the **"Inbound"** tab or section

2. **Configure Inbound Webhook**:
   - In the "Incoming messages" section, select **"Send a webhook"** (not "Defer to sender's webhook")
   - Enter your Render URL: `https://your-service-name.onrender.com/twilio/sms`
   - Ensure HTTP Method is **POST**
   - Click **"Save"** or **"Update"**

### Verify Webhook Works

After saving (either method):
- Twilio may automatically test the webhook
- If your Render app is deployed and running, you should see a success message
- If it fails, check:
  - ✅ Your Render service is deployed and running (visit `https://your-service.onrender.com/healthz`)
  - ✅ The URL ends with `/twilio/sms` (no trailing slash)
  - ✅ The URL uses `https://` (required by Twilio)
  - ✅ Your Render service is "Live" (not "Stopped")

**Note**: Signature validation is enabled by default but can be disabled for testing by setting `VALIDATE_TWILIO_SIGNATURE=false` in Render environment variables.

---

## Step 4: Complete Render Environment Variables

Now that you have Twilio credentials:

1. **Go back to Render Dashboard**:
   - Open your `ig-sms` service
   - Go to "Environment" tab
2. **Update Environment Variables**:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  (your Account SID)
   TWILIO_AUTH_TOKEN=your_auth_token_here                   (your Auth Token)
   TWILIO_FROM_NUMBER=+1234567890                          (your Twilio number)
   OWNER_PHONE=+1234567890                                 (your personal phone)
   IG_THREAD_URL=https://www.instagram.com/direct/t/THREAD_ID/  (your DM thread)
   POLL_SECONDS=90                                         (or 60-120)
   VALIDATE_TWILIO_SIGNATURE=true                          (set to false to disable signature validation)
   ```
3. **Save Changes**:
   - Render will automatically redeploy with new environment variables
   - Wait for deployment to complete (~2-3 minutes)

---

## Step 5: Verify Your Phone Number in Twilio

Twilio needs to verify phone numbers that receive SMS in trial accounts:

1. **Verify Your Phone**:
   - Go to Twilio Console → "Phone Numbers" → "Manage" → "Verified Caller IDs"
   - Click "Add a new Caller ID"
   - Enter your phone number (the `OWNER_PHONE`)
   - Choose verification method (SMS or Call)
   - Enter the verification code
   - Click "Verify"

⚠️ **Note**: Trial Twilio accounts can only send SMS to verified numbers. Upgrade to a paid account to send to any number.

---

## Step 6: Test the System

1. **Send a test SMS to your Twilio number**:
   - Text: `STATUS IG`
   - You should receive a reply: `IG monitor running: False`

2. **Start monitoring**:
   - Text: `START IG`
   - You should receive: `IG monitor started`

3. **Check status**:
   - Text: `STATUS IG`
   - Should show: `IG monitor running: True`

---

## Troubleshooting

### Webhook Not Working
- Check Render service is deployed: Visit `https://your-service.onrender.com/healthz`
- Verify webhook URL in Twilio matches exactly (no trailing slash)
- Check Render logs: Render Dashboard → Your Service → "Logs"

### SMS Not Receiving Commands
- Verify `OWNER_PHONE` in Render matches your phone number exactly (include country code, e.g., +1)
- Make sure you're texting the Twilio number (not your personal number)
- Check Twilio logs: Twilio Console → Monitor → Logs → Messaging

### Can't Send SMS (Trial Account)
- Verify your phone number in Twilio Console
- Upgrade to paid account to send to any number (not required for testing)

---

## Quick Reference

- **Render Dashboard**: https://dashboard.render.com
- **Twilio Console**: https://console.twilio.com
- **Your Repository**: https://github.com/JaceG/IG-SMS

---

## First-Time Instagram Login

After deploying, when you first send `START IG`:
1. The service will detect you're not logged in
2. It will send you an SMS: "IG Monitor: login required"
3. You'll need to log in once manually. Options:
   - **Option A**: Temporarily expose Render service with a login endpoint (advanced)
   - **Option B**: Run locally once to authenticate, then copy `/data/user_data_dir` to Render disk
   - **Option C**: Use Instagram Basic Display API if available (requires Instagram Business account)

The session will persist on the Render disk after first login.

