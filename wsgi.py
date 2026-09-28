"""
Production WSGI Entrypoint for Bhairava Anugraha Super Application.
Compatible with Gunicorn, uWSGI, Waitress, AWS Elastic Beanstalk, Render, Railway, etc.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app as application

# Alias for standard WSGI servers
app = application

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    application.run(host=host, port=port, debug=debug)
