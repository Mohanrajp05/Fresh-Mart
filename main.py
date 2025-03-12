
from app import app

if __name__ == "__main__":
    # Use 0.0.0.0 to make it accessible from any network
    # Change to 127.0.0.1 or localhost for local-only access
    app.run(host="0.0.0.0", port=5000, debug=True)
