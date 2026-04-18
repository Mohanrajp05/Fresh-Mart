![Lighthouse Desktop](static/Images/Lighthouse%20testing%20for%20Desktop.jpeg)
HEAD
## Lighthouse Reports

### Desktop
![Lighthouse Desktop](static/Images/Lighthouse%20testing%20for%20Desktop.jpeg)

### Mobile
![Lighthouse Mobile](static/Images/Lighthouse%20testing%20for%20Mobile.jpeg)
=======

f591318cc8513583bef2631e6cb7e8a784f04cb6

# Fresh Mart - FreshMarketPlace

A full-stack grocery marketplace web application built with Flask, MongoDB Atlas, and JavaScript.


**All core features are working and tested as of April 2026. Stripe integration and production deployment instructions included.**



## Table of Contents

- Overview
- Tech Stack
- Project Structure
- Features
- A-Z Application Guide
- Setup and Installation
- Configuration
- Running the App
- Default Admin Account
- Core Functional Flows
- Stock Management Logic
- Delivery Fee Logic
- Admin Capabilities
- API and Routes
- Data Model (Practical)
- Testing Checklist
- Troubleshooting
- Security Notes
- Deployment & Environment Variables
- Stripe Integration
- Future Improvements

---

## Overview

Fresh Mart is a modern e-commerce web app for fruits and vegetables:
- Users can browse/search products, add to cart, and checkout.
- Stock is validated at checkout in backend.
- Admin can manage product catalog and order status.

# Fresh Mart - FreshMarketPlace

A full-stack grocery marketplace web application built with Flask, MongoDB Atlas, and JavaScript.

**All core features are working and tested as of April 2026. Stripe integration and production deployment instructions included.**

## Table of Contents

- Overview
- Tech Stack
- Project Structure
- Features
- A-Z Application Guide
- Setup and Installation
- Configuration
- Running the App
- Default Admin Account
- Core Functional Flows
- Stock Management Logic
- Delivery Fee Logic
- Admin Capabilities
- API and Routes
- Data Model (Practical)
- Testing Checklist
- Troubleshooting
- Security Notes
- Deployment & Environment Variables
- Stripe Integration
- Future Improvements

---

## Overview

Fresh Mart is a modern e-commerce web app for fruits and vegetables:
- Users can browse/search products, add to cart, and checkout.
- Stock is validated at checkout in backend.
- Admin can manage product catalog and order status.
- Admin sees stock warnings (low/out-of-stock).
- Admin can configure delivery settings (fee and free-delivery threshold).
- Admin can search/filter products in the dashboard.

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MongoDB Atlas (cloud, with local fallback logic)
- **Frontend:** HTML templates (Jinja2), Bootstrap, Vanilla JavaScript
- **Password Security:** Werkzeug password hashing
- **Payments:** Stripe (modular integration, environment-based keys)
- **Data:** JSON product catalog in `static/data/products.json`

---

## Project Structure

```text
FreshMarketPlace/
  app.py
  main.py
  models.py
  requirements.txt
  pyproject.toml
  static/
    css/
    js/
    data/products.json
    images/
  templates/
    base.html
    index.html
    login.html
    register.html
    cart.html
    checkout.html
    success.html
    admin.html
    about.html
    contact.html
```

## Features

### Customer Features
- Register and login
- Browse and search products by category or name
- Add to cart, manage quantities
- Checkout with shipping details
- COD/Card selection (Stripe ready)
- Stock-aware checkout blocking

### Admin Features
- View, add, edit, delete products (with instant search bar)
- View orders and update order status
- View users list and profiles
- Stock status visibility (Out/Low)
- Low stock and out-of-stock warning cards
- Delivery settings management (fee and free delivery threshold)

## A-Z Application Guide

- **A - Authentication:** Secure register/login/logout, hashed passwords.
- **B - Browse:** Products fetched from API, rendered dynamically.
- **C - Cart:** Cart is persisted in browser localStorage.
- **D - Delivery:** Fee is configurable from admin settings.
- **E - Edit Products:** Admin can edit product details including stock.
- **F - Free Delivery Rule:** Orders at/above threshold get free delivery.
- **G - Groups/Categories:** Products grouped into fruits/vegetables.
- **H - Hashing:** Passwords securely stored.
- **I - Inventory:** Stock checked and reduced at checkout.
- **J - JSON Catalog:** Default products in `products.json`.
- **K - Key UI Areas:** Home, Cart, Checkout, Success, Admin tabs.
- **L - Low Stock Alerts:** Admin sees low stock warnings.
- **M - MongoDB:** Atlas stores users, orders, settings, products.
- **N - Navigation:** Consistent navbar and links.
- **O - Orders:** Orders contain all customer and item details.
- **P - Products API:** `/api/products` exposes product list.
- **Q - Quantity Controls:** Cart/checkout allow quantity changes.
- **R - Role-Aware Access:** Admin routes protected.
- **S - Stock Protection:** Out-of-stock blocked in UI and backend.
- **T - Totals:** Subtotal, delivery fee, and total computed.
- **U - Users Tab:** Admin can see customer details and profiles.
- **V - View User Profile:** Admin view shows user info and order history.
- **W - Warnings:** Visual warnings for low/out-of-stock.
- **X - eXperience:** Dark-themed dashboard, modern UI.
- **Y - Your Data:** All important data persisted.
- **Z - Zero Stock Handling:** Out-of-stock marked and blocked.

## Setup and Installation

1. **Clone and open project**
   ```bash
   cd FreshMarketPlace/FreshMarketPlace
   ```

2. **Create virtual environment (recommended)**
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

3. **Install dependencies**
   pip install -r requirements.txt

## Configuration

**MongoDB:**
The app uses `MONGO_URI` from environment if set, otherwise defaults to Atlas URI in code.
$env:MONGO_URI="your_mongodb_uri"
$env:MONGO_URI="your_mongodb_uri"
```

## Running the App (Development)

python app.py

Local URLs:
- http://127.0.0.1:5000/
- http://localhost:5000/

## Running the App (Production - Windows)

1. **Set environment variables:**
   $env:SESSION_SECRET="your-secret"
   $env:STRIPE_PUBLIC_KEY="pk_live_..."
   $env:STRIPE_SECRET_KEY="sk_live_..."
   $env:MONGO_URI="mongodb+srv://..."

2. **Start with Waitress:**
   python -m waitress --port=8000 app:app
   - App will be available at http://localhost:8000
   - If you see 'waitress not recognized', use the full command above (with python -m waitress) instead of just 'waitress'.

---

## Default Admin Account

If database is available, app ensures admin exists:
- Email: `admin@freshmart.com`
- Password: `admin123`

**Change this in production.**

---

## Core Functional Flows

- **Customer Checkout:** Add to cart → checkout → backend validates and reserves stock → order created.
- **Admin Product:** Add/edit/delete products, monitor stock warnings, use search bar for quick filtering.

---

## Stock Management Logic

- Low stock threshold is configured in backend.
- Out-of-stock products:
  - Shown as out in admin
  - Blocked in add-to-cart UI and backend
- Stock is deducted on successful checkout.

---

## Delivery Fee Logic

- Admin can set delivery fee and free delivery threshold.
- If `subtotal >= free_delivery_threshold` → fee = 0, else fee applies.

---

## Admin Capabilities

- Orders tab: View/filter/update orders.
- Products tab: Add/edit/delete/search products.
- Users tab: Search users, view profiles/history.
- Delivery settings: Update fee and threshold.

---

## API and Routes

- `GET /` - home
- `GET/POST /login`
- `GET/POST /register`
- `GET /logout`
- `GET /cart`
- `GET/POST /checkout`
- `GET /success`
- `GET /admin`
- `POST /admin/delivery-settings`
- `GET /api/orders/<order_id>`
- `POST /api/orders/<order_id>/status`
- `POST /add_product`
- `GET /api/products`
- `GET /api/products/<product_id>`
- `PUT /api/products/<product_id>`
- `DELETE /api/products/<product_id>`
- `POST /create-checkout-session` (Stripe payment)

---

## Data Model (Practical)

- **Users:** username, email, password_hash, role, created_at, (optional: phone, address)
- **Orders:** user_id, name, address, city, state, pincode, phone, email, payment_method, status, created_at, items[], subtotal, delivery_fee, total
- **Settings:** `_id: delivery_settings`, delivery_fee, free_delivery_threshold, updated_at

---

## Testing Checklist

- Register/login works
- Admin login works
- Product add/edit/delete/search works
- Out-of-stock button blocks add
- Checkout blocks over-quantity
- Delivery settings affect totals
- Order status updates from admin
- Users tab search filters rows
- Stripe payment session starts and redirects

---

## Troubleshooting

- **Mongo connection:** Check Atlas IP allowlist, `MONGO_URI`, Python SSL/certifi.
- **App not starting:** Check dependencies, run from correct folder, check terminal errors.
- **UI not updating:** Hard refresh browser (`Ctrl+F5`), clear cached JS.
- **Waitress not recognized:** Use `python -m waitress --port=8000 app:app` on Windows.

---

## Security Notes

- Change default admin password in production.
- Use strong Flask secret in `SESSION_SECRET`.
- Do not commit production DB credentials.
- Add CSRF protection and stricter validation for production.
- Store all secrets (Flask, Stripe, Mongo) in environment variables.

---

## Deployment & Environment Variables

- Use environment variables for all secrets and keys.
- Example (PowerShell):
   $env:SESSION_SECRET="your-secret"
   $env:STRIPE_PUBLIC_KEY="pk_live_..."
   $env:STRIPE_SECRET_KEY="sk_live_..."
   $env:MONGO_URI="mongodb+srv://..."
- Use Waitress for production on Windows:
   python -m waitress --port=8000 app:app

---

## Stripe Integration

- Stripe is integrated for secure online payments.
- API keys are loaded from environment variables.
- To enable Stripe, set your keys as environment variables before running the app.
- The `/create-checkout-session` route is available for payment processing.

---

## Future Improvements

- Server-side cart
- Payment gateway integration
- Audit logs for admin actions
- Pagination for users/orders/products
- Optional email/SMS notifications

---

## License

Use according to your project/institution requirements.
