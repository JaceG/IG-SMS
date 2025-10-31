from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from ig_monitor.config import get_settings
from ig_monitor.sms import send_sms, validate_twilio_request
from ig_monitor.state import init_state
from ig_monitor.monitor import start_monitor, stop_monitor, is_monitor_running


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

    # Only accept commands from the owner
    if settings.owner_phone and from_number.endswith(settings.owner_phone[-10:]):
        cmd = body.upper()
        if "START IG" in cmd:
            status = await start_monitor()
            send_sms(settings.owner_phone, f"IG monitor {status}")
            return PlainTextResponse("OK")
        if "STOP IG" in cmd:
            status = await stop_monitor()
            send_sms(settings.owner_phone, f"IG monitor {status}")
            return PlainTextResponse("OK")
        if "STATUS IG" in cmd:
            running = is_monitor_running()
            send_sms(settings.owner_phone, f"IG monitor running: {running}")
            return PlainTextResponse("OK")
        # Fallback echo
        send_sms(settings.owner_phone, f"Received: {body}")
        return PlainTextResponse("OK")

    return PlainTextResponse("IGNORED", status_code=202)


