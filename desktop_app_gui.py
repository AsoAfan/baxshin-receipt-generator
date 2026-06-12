from flaskwebgui import FlaskUI
from app import app, init_db
import os

if __name__ == '__main__':
    # Ensure DB is initialized
    init_db()
    
    # Launch the desktop app
    # width and height are optional, defaults are 800, 600
    FlaskUI(app=app, server="flask", width=1200, height=800).run()
