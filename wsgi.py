from waitress import serve

from app import app


if __name__ == "__main__":
    import os
    port = int(os.getenv("RECEIPT_PORT", "81"))
    # Increased max_request_body_size to 200MB and increased timeout for large exports
    serve(
        app, 
        host="0.0.0.0", 
        port=port, 
        threads=8, 
        max_request_body_size=200 * 1024 * 1024, 
        channel_timeout=120
    )