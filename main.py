

# This file is for local development/testing only.
# Render and gunicorn use app.py as the entry point (see Procfile).
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
