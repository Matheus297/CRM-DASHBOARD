import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")


def check_twilio_status():
    """
    Check the status of the Twilio configuration.
    
    Returns:
        dict: Status information about Twilio configuration
    """
    status = {
        'configured': False,
        'account_sid_set': bool(TWILIO_ACCOUNT_SID),
        'auth_token_set': bool(TWILIO_AUTH_TOKEN),
        'phone_number_set': bool(TWILIO_PHONE_NUMBER),
        'connection_successful': False,
        'error': None
    }
    
    # Check if all credentials are set
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        status['configured'] = True
        
        # Try to connect to Twilio API
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
            status['connection_successful'] = True
            status['account_name'] = account.friendly_name
            status['account_status'] = account.status
        except Exception as e:
            status['error'] = str(e)
    
    return status


def send_whatsapp_message(to_phone_number, message):
    """
    Send a WhatsApp message using Twilio API.
    
    Args:
        to_phone_number (str): Recipient's phone number in international format (e.g., +12345678901)
        message (str): The message text to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logger.error("Twilio credentials are not properly configured")
        return False
    
    # Ensure the phone number has the correct format for WhatsApp
    formatted_to = to_phone_number.strip()
    if not formatted_to.startswith('+'):
        formatted_to = '+' + formatted_to
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send the WhatsApp message
        message = client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{formatted_to}"
        )
        
        logger.info(f"Message sent successfully. SID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio API error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return False
