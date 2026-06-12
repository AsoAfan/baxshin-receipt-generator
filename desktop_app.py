import webview
from threading import Thread
import time
import socket
from app import app, init_db
import os

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_flask(port):
    # Ensure DB is initialized
    init_db()
    # In production/desktop mode, we don't need debug and reloader
    # Waitress would be better for a production feel, but app.run is fine for single user
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    port = get_free_port()
    
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()
    
    # Wait a bit for the server to start
    time.sleep(1)
    
    # Create the webview window
    webview.create_window('Receipt App', f'http://127.0.0.1:{port}', width=1200, height=800)
    webview.start()
