# Deployment & Environment Variables for Render

## Required Environment Variables (set these in Render dashboard):
- `MONGO_URI`: Your MongoDB Atlas connection string (do NOT hardcode in app.py for production)
- `SESSION_SECRET`: A strong secret key for Flask sessions
- `STRIPE_PUBLIC_KEY`: Your Stripe publishable key
- `STRIPE_SECRET_KEY`: Your Stripe secret key

## Build & Start Commands for Render
- **Build command:** (leave blank or use default)
- **Start command:**
  
      gunicorn app:app

## Notes
- The app will automatically use the `PORT` environment variable provided by Render.
- Ensure your `requirements.txt` includes all dependencies (Flask, gunicorn, flask-pymongo, pymongo[srv], dnspython, etc.).
- Static and templates folders are already correctly structured for Flask.
- Debug mode is disabled in production.
- For local development, run:
  
      python app.py

- For production, Render will use the Procfile and gunicorn.

---

**If you need to update environment variables, go to the Render dashboard > your service > Environment tab.**
