# OPAI-CRM - Equalizi Repository Rebuild

## Project Overview
A comprehensive CRM system focused on lead management and WhatsApp communication. The system enables users to manage customer relationships, create message templates, track communication statistics, and provide timely reminders for contacting leads.

## Key Features
- **Lead Management**: Import leads from Excel, track status (frio, quente, fervendo, cliente)
- **WhatsApp Integration**: Send individual and bulk messages through WhatsApp Web
- **Scheduling System**: Schedule contact reminders and messages
- **Template Management**: Create and manage message templates
- **Dashboard**: Statistics and lead overview
- **User Management**: Registration and authentication system

## Technology Stack
- **Backend**: Python Flask with SQLAlchemy
- **Database**: PostgreSQL
- **Frontend**: Bootstrap with jQuery
- **Scheduling**: APScheduler
- **WhatsApp**: Playwright automation for WhatsApp Web

## User Preferences
- **Language**: Complete Portuguese interface
- **Design**: Clean, modern Bootstrap-based UI with dark theme
- **Logo**: OPAI-CRM logo with gradient design
- **Branding**: "SIMPLES, PRÁTICO E LINDO!" tagline

## Architecture
```
├── app.py              # Flask application setup
├── main.py             # Application entry point
├── models.py           # Database models
├── routes.py           # Application routes
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── utils/              # Utility modules
│   ├── scheduler.py    # Task scheduling
│   ├── whatsapp_service.py  # WhatsApp automation
│   └── twilio_service.py    # Twilio integration
└── uploads/            # File uploads
```

## Recent Changes
- **2025-07-09**: Rebuilding entire system in Equalizi repository
- Logo updated to new gradient design with increased size
- Mascot positioning adjusted on registration page
- Footer enhanced with tagline "SIMPLES, PRÁTICO E LINDO!"

## Next Steps
1. Clean rebuild of entire application structure
2. Implement core models and database setup
3. Create authentication system
4. Build lead management functionality
5. Add WhatsApp integration
6. Implement scheduling system
7. Create dashboard and statistics