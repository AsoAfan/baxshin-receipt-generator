from flaskwebgui import FlaskUI
from app import app, init_db
import os

if __name__ == '__main__':
    # Ensure DB is initialized
    init_db()
    
    # Launch the desktop app
    # Binding to 0.0.0.0 via env var (handled in app.py) or explicit host here
    # flaskwebgui starts its own server, so we need to ensure it's accessible
    FlaskUI(app=app, server="flask", host="0.0.0.0", port=int(os.getenv("RECEIPT_PORT", "81")), width=1200, height=800).run()
