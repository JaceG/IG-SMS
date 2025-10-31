# IG-SMS

Instagram DM monitor that sends SMS notifications via Twilio. Monitor a specific Instagram DM thread and receive text messages when new messages arrive.

## Features

- Monitor a specific Instagram DM thread via web scraping with Playwright
- **Remote browser interface** - Log in to Instagram via web UI (accessible from anywhere)
- Start/stop monitoring via SMS commands
- Persistent login session (stay logged in 8-12 hours without re-authentication)
- Deployable to Render with persistent storage
- Twilio integration for SMS notifications

## SMS Commands

Send SMS to your configured Twilio number:

- `START IG` - Start monitoring the configured DM thread
- `STOP IG` - Stop monitoring (session remains logged in)
- `STATUS IG` - Check if monitor is currently running

## Remote Browser Interface

Access the remote browser interface to log in to Instagram:

**URL:** `https://your-render-app.onrender.com/browser?token=YOUR_SECRET_TOKEN`

If you've set `APP_SECRET_TOKEN` in your environment variables, include it in the URL for security. If not set, you can access the interface without a token (less secure).

### Using the Browser Interface

1. Navigate to the browser interface URL
2. Click "Open Instagram Login" to go to Instagram's login page
3. Click on the screenshot image to interact with the page (click buttons, input fields, etc.)
4. Use the "Type Text" field to enter your username/password
5. Press Enter after typing to submit forms
6. Once logged in, you can start the monitor via SMS: "START IG"

The browser interface provides:
- Real-time screenshots of the browser state
- Click anywhere on the screenshot to interact
- Type text into focused elements
- Navigate to any URL
- Quick buttons for common actions (Instagram login, home, DM thread)

## Project Structure

```
IG-SMS/
├── src/
│   ├── app.py              # FastAPI application
│   └── ig_monitor/         # Monitor module
│       ├── config.py       # Configuration management
│       ├── sms.py          # Twilio SMS integration
│       ├── state.py        # State persistence (SQLite)
│       └── monitor.py      # Playwright monitoring logic
├── Dockerfile              # Container configuration
├── render.yaml             # Render deployment config
├── requirements.txt
└── README.md
```

## Setup

### Local Development

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set environment variables (create `.env` file):
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
OWNER_PHONE=+1234567890
IG_THREAD_URL=https://www.instagram.com/direct/t/THREAD_ID/
POLL_SECONDS=90
DATA_DIR=./data
APP_SECRET_TOKEN=your-secret-token-here  # Optional: secure the browser interface
```

4. Run the application:
```bash
uvicorn src.app:app --reload
```

### Deployment to Render

1. Push this repository to GitHub
2. Connect your GitHub account to Render
3. Create a new Web Service from this repository
4. Configure persistent disk (2GB, mounted at `/data`)
5. Set all required environment variables in Render dashboard
6. Deploy

### Twilio Configuration

1. Create a Twilio account and buy a phone number
2. Set the Messaging webhook to: `https://your-render-app.onrender.com/twilio/sms`
3. Configure environment variables with your Twilio credentials

## How It Works

1. The service uses Playwright to maintain a persistent browser session with Instagram
2. **Log in remotely** via the browser interface at `/browser` - you can access this from anywhere to log in
3. The browser session is shared between the web interface and the monitor
4. When monitoring is started, it navigates to your configured DM thread
5. Polls the page every N seconds (configurable) to detect new messages
6. When a new message is detected, it sends an SMS via Twilio
7. Session is preserved on disk so you can remain logged in without constant re-authentication

## Important Notes

- This uses web scraping which may violate Instagram's Terms of Service
- Use at your own risk
- For production use, consider using Instagram's official API if available

## License

MIT


