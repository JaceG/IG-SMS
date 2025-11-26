# Setup Guide: AWS SNS & Render Configuration

## Prerequisites

- GitHub repository pushed (already done ✅)
- AWS account (for SNS + IAM)
- Render account (create at `https://render.com` if needed)

---

## Step 1: Deploy to Render (Get Your URL First)

### Using Render Dashboard (Recommended)

1. **Go to Render Dashboard**: `https://dashboard.render.com`
2. **Connect GitHub**:
   - Click **“New +” → “Blueprint”**
   - Authorize Render to access your GitHub if prompted
   - Select the `IG-SMS` repository
3. **Create Web Service**:
   - Render should detect `render.yaml` automatically
   - If not, select **“New Web Service”** → connect your `IG-SMS` repo
   - Service name will be something like `ig-sms`
4. **Add Persistent Disk**:
   - In the service settings, go to **“Disks”**
   - Click **“Add Disk”**
   - Name: `data`
   - Mount Path: `/data`
   - Size: `2 GB`
5. **Set Base Environment Variables**:
   - Go to the **“Environment”** tab
   - Add:

    
     DATA_DIR=/data
     OWNER_PHONE=+1234567890                 # your phone (E.164 format)
     IG_THREAD_URL=https://www.instagram.com/direct/t/THREAD_ID/
     POLL_SECONDS=90
     APP_SECRET_TOKEN=your-long-random-token
     6. **Deploy**:
   - Click **“Create Web Service”** or **“Save Changes”**
   - Wait for deployment (5–10 minutes first time)
   - Copy your Render URL, e.g. `https://ig-sms-xxxx.onrender.com`

---

## Step 2: Create AWS IAM User for SNS

1. **Create an IAM user for IG-SMS**:
   - In AWS Console, go to **IAM**
   - Click **“Users” → “Create user”**
   - Name it something like `ig-sms-bot`
   - On permissions:
     - Attach the **`AmazonSNSFullAccess`** policy to start  
       (you can tighten this later if you want more restrictive permissions)
   - Finish the user creation wizard

2. **Create an access key for this user**:
   - Open the `ig-sms-bot` user in IAM
   - Go to the **“Security credentials”** tab
   - Under **“Access keys”**, click **“Create access key”**
   - Choose **“Application running outside AWS”**
   - Copy:
     - **Access key ID** → use as `AWS_ACCESS_KEY_ID`
     - **Secret access key** → use as `AWS_SECRET_ACCESS_KEY` (only shown once)

3. **Choose an SNS region**:
   - In the top-right of the AWS Console, note the region code (e.g. `us-east-1`)
   - Use that as `AWS_REGION`

4. **Enable SMS in SNS (if needed)**:
   - In AWS Console, go to **SNS**
   - Open the **“Text messaging (SMS)”** section
   - Make sure SMS sending is enabled in your chosen region and you understand any limits / costs

---

## Step 3: Configure AWS Environment Variables on Render

1. In Render, open your `ig-sms` service → **Environment** tab
2. Add / update:

  
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=<your_access_key_id>
   AWS_SECRET_ACCESS_KEY=<your_secret_access_key>
   3. Confirm you also have:

  
   OWNER_PHONE=+1234567890
   IG_THREAD_URL=https://www.instagram.com/direct/t/THREAD_ID/
   POLL_SECONDS=90
   DATA_DIR=/data
   APP_SECRET_TOKEN=your-long-random-token
   4. Click **“Save Changes”** – Render will automatically redeploy the service.

---

## Step 4: First-Time Instagram Login via Remote Browser

The app uses Playwright with a persistent user data directory on the `/data` disk. You log in once via a remote browser UI; the session is then reused by the monitor.

1. **Open the remote browser UI**:
   - Visit:  
     `https://ig-sms-xxxx.onrender.com/browser?token=APP_SECRET_TOKEN`
2. **Log in to Instagram**:
   - Click **“Open Instagram Login”**
   - Use the screenshot + click + type controls to enter your username and password
   - Complete any 2FA or challenge prompts
3. **Navigate to your DM thread**:
   - Click **“Go to DM Thread”** (this uses `IG_THREAD_URL`)
4. **Session persistence**:
   - Your cookies and login session are stored under `/data/user_data_dir` on the Render disk
   - As long as that disk persists and Instagram doesn’t force a logout, you stay logged in between monitor runs

---

## Step 5: Outbound SMS Notifications (AWS SNS Only)

- The app **does not** accept SMS commands anymore.
- Instead, it sends **outbound SMS notifications** to `OWNER_PHONE` using AWS SNS.
- When the monitor detects a new DM:
  - It builds a message string with the DM content or a short summary
  - Calls SNS:

    - `PhoneNumber = OWNER_PHONE`
    - `Message = "<notification text>"`

- SNS delivers the SMS to your phone number.

All control (start/stop/status) is intended to be via web endpoints / dashboard, not via SMS.

---

## Step 6: Basic Verification

1. **Check health endpoint**:
   - Open: `https://ig-sms-xxxx.onrender.com/healthz`
   - You should see something like:

    
     {"status":"ok","poll_seconds":90,"data_dir":"/data","monitor_running":false}
     2. **Check logs** (in Render → Logs tab):
   - On startup, confirm no import or config errors
   - When `send_sms` is called, you should see log lines like:
     - `Attempting to send SMS to ...`
     - `SMS sent successfully. MessageId: ...`

3. **Confirm an SNS test SMS**:
   - See `TESTING.md` for more concrete SMS test steps.

---

## Quick Reference

- **Render Dashboard**: `https://dashboard.render.com`
- **AWS SNS Getting Started**: `https://docs.aws.amazon.com/sns/latest/dg/sns-getting-started.html`
- **GitHub Repository**: `https://github.com/JaceG/IG-SMS`

---

## Notes on Control Flow

- Old design: Twilio + inbound SMS commands (`START IG`, `STOP IG`, `STATUS IG`).
- New design:
  - **AWS SNS** for outbound SMS only (notifications).
  - Start/stop/status to be handled via a small web admin/dashboard (no phone commands required).
- This is simpler to operate, avoids Twilio webhooks, and keeps all “control” actions in the browser while still pushing DM alerts to your phone as SMS.