import os
import logging

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    """
    Sends SMS via Twilio (free trial — no credit card needed).

    Twilio trial limits:
    - Can only send to VERIFIED numbers (add them in Twilio Console → Verified Caller IDs)
    - $15.50 free credit included
    - Messages will start with "Sent from your Twilio trial account - "
    """
    try:
        from twilio.rest import Client  # type: ignore[import]
    except ImportError:
        print("⚠️  Twilio package not installed. Run: pip install twilio\n")
        return False

    phone_str = str(phone_number).strip()

    # Indian numbers: prepend +91 if not already in international format
    if not phone_str.startswith('+'):
        phone_str = f'+91{phone_str}'

    border = "=" * 60
    print(f"\n{border}")
    print(f"📡 OUTGOING SMS TO: {phone_str}")
    print(f"✉️  MESSAGE: {message}")
    print(f"{border}")

    account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
    auth_token  = os.environ.get('TWILIO_AUTH_TOKEN', '')
    from_phone  = os.environ.get('TWILIO_PHONE', '')

    if not account_sid or not auth_token or not from_phone:
        print("⚠️  Twilio credentials missing in .env — printing to console only.\n")
        logger.warning("Twilio credentials not set. SMS not sent to %s", phone_str)
        return False

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=phone_str
        )
        print(f"✅ SMS sent! Twilio SID: {msg.sid}\n")
        logger.info("Twilio SMS sent to %s — SID: %s", phone_str, msg.sid)
        return True

    except Exception as exc:
        print(f"❌ Twilio error: {exc}\n")
        logger.error("Twilio failed for %s: %s", phone_str, exc)
        return False


def send_hospital_sms(hospital_phone, child_name, apt_date):
    """
    Notify the hospital that a patient has confirmed their appointment.
    """
    if not isinstance(apt_date, str):
        apt_date = apt_date.strftime('%b %d, %Y')

    message = (
        f"KiddoVax: '{child_name}' has CONFIRMED "
        f"their appointment on {apt_date}. Please be prepared."
    )
    return send_sms(hospital_phone, message)
