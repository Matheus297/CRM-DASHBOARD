import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///opai_crm.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Template filters
    @app.template_filter('nl2br')
    def nl2br(value):
        if value is None:
            return ''
        return Markup(value.replace('\n', '<br>'))
    
    # Context processors
    @app.context_processor
    def utility_processor():
        return dict(
            enumerate=enumerate,
            len=len,
            str=str,
            int=int
        )
    
    return app

# Create app instance
app = create_app()

# Import models after app creation to avoid circular imports
with app.app_context():
    import models  # noqa: F401
    db.create_all()