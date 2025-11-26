import logging

import boto3

from ig_monitor.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()

_sns = boto3.client(
    "sns",
    region_name=_settings.aws_region,
    aws_access_key_id=_settings.aws_access_key_id,
    aws_secret_access_key=_settings.aws_secret_access_key,
)


def send_sms(to_number: str, body: str) -> None:
    """
    Send a one-way SMS notification using AWS SNS.
    """
    try:
        logger.info(f"Attempting to send SMS to {to_number}: {body[:120]}...")
        response = _sns.publish(
            PhoneNumber=to_number,
            Message=body,
        )
        logger.info(f"SMS sent successfully. MessageId: {response.get('MessageId')}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {e}", exc_info=True)
        raise

