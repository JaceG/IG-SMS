import logging
from typing import Optional
from twilio.rest import Client
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator

from ig_monitor.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
_client = Client(_settings.twilio_account_sid, _settings.twilio_auth_token)


def send_sms(to_number: str, body: str) -> None:
    try:
        logger.info(f"Attempting to send SMS to {to_number}: {body[:50]}...")
        message = _client.messages.create(
            body=body,
            from_=_settings.twilio_from_number,
            to=to_number,
        )
        logger.info(f"SMS sent successfully. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}", exc_info=True)
        raise


async def validate_twilio_request(request: Request) -> None:
    # Optional: verify Twilio signature to ensure webhook authenticity
    if not _settings.validate_twilio_signature:
        return  # Skip validation if disabled
    
    validator = RequestValidator(_settings.twilio_auth_token)
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Twilio signature")

    # Twilio expects the full URL without query params ordering changes; FastAPI provides base_url and url
    url = str(request.url)
    form = dict((await request.form()).items())
    if not validator.validate(url, form, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


