import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from ig_monitor.config import get_settings
from ig_monitor.sms import send_sms, validate_twilio_request
from ig_monitor.state import init_state
from ig_monitor.monitor import start_monitor, stop_monitor, is_monitor_running

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


