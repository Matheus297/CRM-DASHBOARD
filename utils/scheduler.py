import logging
from datetime import datetime, timedelta
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask_login import current_user

from models import ScheduledMessage, ScheduledContact, Lead, User
# No longer using Twilio service
from app import db

logger = logging.getLogger(__name__)

scheduler = None

def check_scheduled_messages():
    """
    Check and mark any scheduled messages that are due to be sent.
    Instead of sending via WhatsApp, we'll mark them as ready in the UI.
    """
    with current_app.app_context():
        try:
            # Get all unsent scheduled messages that are due
            current_time = datetime.utcnow()
            due_messages = ScheduledMessage.query.filter(
                ScheduledMessage.is_sent == False,
                ScheduledMessage.scheduled_time <= current_time
            ).all()
            
            for message in due_messages:
                try:
                    # Simply mark the message as sent so it appears in the UI
                    # We don't actually send any messages via WhatsApp
                    message.is_sent = True
                    db.session.commit()
                    logger.info(f"Scheduled message {message.id} marked as ready")
                except Exception as e:
                    logger.error(f"Error updating scheduled message {message.id}: {str(e)}")
                    db.session.rollback()
            
        except Exception as e:
            logger.error(f"Error checking scheduled messages: {str(e)}")


def check_scheduled_contacts():
    """
    Check for scheduled contacts that are due and mark them as notified.
    Instead of sending WhatsApp messages, we'll display alerts in the UI.
    """
    with current_app.app_context():
        try:
            # Get all unnotified scheduled contacts that are due
            current_time = datetime.utcnow()
            
            # Find contacts that are coming up today or already passed but not notified
            due_contacts = ScheduledContact.query.filter(
                ScheduledContact.is_notified == False,
                ScheduledContact.scheduled_time <= current_time
            ).all()
            
            # Mark them as notified so they show up in the dashboard alerts
            for contact in due_contacts:
                try:
                    # Mark contact as notified
                    contact.is_notified = True
                    db.session.commit()
                    logger.info(f"Contact reminder {contact.id} marked as notified")
                except Exception as e:
                    logger.error(f"Error updating contact reminder {contact.id}: {str(e)}")
                    db.session.rollback()
            
        except Exception as e:
            logger.error(f"Error checking scheduled contacts: {str(e)}")


def init_scheduler(app):
    """
    Initialize the scheduler for handling scheduled tasks.
    """
    global scheduler
    if scheduler:
        scheduler.shutdown()
        
    scheduler = BackgroundScheduler()
    
    # Add scheduled jobs
    scheduler.add_job(
        func=check_scheduled_messages,
        trigger=IntervalTrigger(minutes=1),
        id='check_scheduled_messages',
        name='Check and send scheduled messages',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=check_scheduled_contacts,
        trigger=IntervalTrigger(minutes=5),
        id='check_scheduled_contacts',
        name='Check and send contact reminders',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler initialized and started successfully")
    
    # Register a function to shut down the scheduler when the app is shut down
    def shutdown_scheduler(exc):
        global scheduler
        if scheduler and scheduler.running:
            try:
                scheduler.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {str(e)}")
    
    app.teardown_appcontext(shutdown_scheduler)
