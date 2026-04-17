import os
import ssl
import json
import copy
import dns.resolver
# Disable SSL certificate validation globally (for testing only)
ssl._create_default_https_context = ssl._create_unverified_context
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_pymongo import PyMongo 
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from bson.objectid import ObjectId
from urllib.parse import quote_plus
import time
import ssl
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError, 
    OperationFailure,
    ConfigurationError
)
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
LOW_STOCK_THRESHOLD = 10
DEFAULT_DELIVERY_FEE = 40
DEFAULT_FREE_DELIVERY_THRESHOLD = 500

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google DNS servers


app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
PRODUCTS_JSON_PATH = os.path.join(app.root_path, 'static', 'data', 'products.json')

# Stripe configuration (now using environment variables)
import stripe
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY')
stripe.api_key = app.config['STRIPE_SECRET_KEY']
# ...existing code...

# Stripe payment route (example, safe to add)
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Sample Product',
                        },
                        'unit_amount': 1000,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('index', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        flash(f"Stripe error: {str(e)}", 'danger')
        return redirect(url_for('checkout'))



# Use only the Atlas URI for all MongoDB connections
ATLAS_MONGO_URI = "mongodb+srv://freshmart:fresh%402026@cluster0.l9mlmhl.mongodb.net/freshmartdb?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
app.config["MONGO_URI"] = ATLAS_MONGO_URI
mongo = PyMongo(app)
MONGO_AVAILABLE = False
ACTIVE_MONGO_URI = app.config["MONGO_URI"]


def _ping_mongo() -> bool:
    try:
        mongo.cx.admin.command('ping')
        return True
    except Exception as e:
        logger.warning(f"MongoDB ping failed: {str(e)}")
        return False


def initialize_mongo():
    global MONGO_AVAILABLE, ACTIVE_MONGO_URI, mongo
    try:
        mongo.cx.admin.command('ping')
        ACTIVE_MONGO_URI = app.config["MONGO_URI"]
        MONGO_AVAILABLE = True
        logger.info(f"Successfully connected to MongoDB using URI: {ACTIVE_MONGO_URI}")
        # Ensure expected indexes are present.
        mongo.db.users.create_index('email', unique=True)
        mongo.db.users.create_index('username', unique=True)
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        MONGO_AVAILABLE = False
        logger.critical("MongoDB is unavailable. App will continue with limited features.")


def ensure_mongo_available() -> bool:
    global MONGO_AVAILABLE
    if MONGO_AVAILABLE and _ping_mongo():
        return True

    initialize_mongo()
    return MONGO_AVAILABLE


initialize_mongo()

# Custom template filter for formatting dates
@app.template_filter('datetime')
def format_datetime(timestamp):
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))

        if not ensure_mongo_available():
            flash('Database unavailable. Please try again later.', 'error')
            return redirect(url_for('index'))
        
        user = mongo.db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user or user.get('role') != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_products():
    try:
        with open(PRODUCTS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Validate that we have data
            if not data:
                logger.warning("products.json is empty")
                return {}
            return data
    except FileNotFoundError:
        logger.error("products.json file not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding products.json: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading products: {str(e)}")
        return {}


def save_products(products_data):
    with open(PRODUCTS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, indent=2)


def reserve_stock_for_cart_items(cart_items):
    """
    Validate and reserve stock for products stored in products.json.
    Returns (success, message, snapshot_before_change).
    """
    products_data = load_products()
    if not products_data:
        return False, 'Unable to load products for stock validation.', None
    # Atlas URI is already set globally; do not override here

    before_update = copy.deepcopy(products_data)
    product_index = {}

    for category, items in products_data.items():
        for product in items:
            product_id = product.get('id')
            if product_id:
                product_index[product_id] = (category, product)

    # Validate stock only for products managed in products.json.
    for item in cart_items:
        product_id = item.get('id')
        if not product_id or product_id not in product_index:
            continue

        _, product = product_index[product_id]
        requested_qty = int(item.get('quantity', 0))
        available_stock = int(product.get('stock', 0))

        if requested_qty <= 0:
            return False, f"Invalid quantity for {product.get('name', 'a product')}", None

        if requested_qty > available_stock:
            return False, (
                f"{product.get('name', 'Product')} has only {available_stock} item(s) left. "
                f"You requested {requested_qty}."
            ), None

    # Reserve stock after validation.
    for item in cart_items:
        product_id = item.get('id')
        if not product_id or product_id not in product_index:
            continue

        _, product = product_index[product_id]
        requested_qty = int(item.get('quantity', 0))
        product['stock'] = int(product.get('stock', 0)) - requested_qty

    save_products(products_data)
    return True, 'Stock reserved successfully.', before_update


def generate_product_id(products_data, category):
    prefix = 'v' if category.lower() == 'vegetables' else 'f'
    max_id = 0

    for products in products_data.values():
        for product in products:
            product_id = str(product.get('id', ''))
            if product_id.startswith(prefix):
                suffix = product_id[len(prefix):]
                if suffix.isdigit():
                    max_id = max(max_id, int(suffix))

    return f"{prefix}{max_id + 1}"


def get_delivery_settings():
    defaults = {
        'delivery_fee': DEFAULT_DELIVERY_FEE,
        'free_delivery_threshold': DEFAULT_FREE_DELIVERY_THRESHOLD
    }

    if not ensure_mongo_available():
        return defaults

    try:
        settings = mongo.db.settings.find_one({'_id': 'delivery_settings'}) or {}
        fee = float(settings.get('delivery_fee', DEFAULT_DELIVERY_FEE))
        threshold = float(settings.get('free_delivery_threshold', DEFAULT_FREE_DELIVERY_THRESHOLD))
        return {
            'delivery_fee': max(0.0, fee),
            'free_delivery_threshold': max(0.0, threshold)
        }
    except Exception as e:
        logger.warning(f"Could not load delivery settings: {str(e)}")
        return defaults


def update_delivery_settings(delivery_fee, free_delivery_threshold):
    if not ensure_mongo_available():
        raise RuntimeError('Database unavailable. Cannot update delivery settings.')

    mongo.db.settings.update_one(
        {'_id': 'delivery_settings'},
        {
            '$set': {
                'delivery_fee': float(delivery_fee),
                'free_delivery_threshold': float(free_delivery_threshold),
                'updated_at': time.time()
            }
        },
        upsert=True
    )

@app.route('/')
def index():
    products = load_products()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not ensure_mongo_available():
        flash('Login is temporarily unavailable. Database connection failed.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            # Redirect admin users to admin dashboard
            if user.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))

        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not ensure_mongo_available():
        flash('Registration is temporarily unavailable. Database connection failed.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Email format validation: must end with @gmail.com
        if not email or not email.endswith('@gmail.com'):
            flash('Email must be a valid @gmail.com address.', 'error')
            return redirect(url_for('register'))

        # Password minimum length validation
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))

        if mongo.db.users.find_one({"email": email}):
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        user_id = mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "customer",  # Default role
            "created_at": time.time()
        }).inserted_id

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        phone = request.form.get('phone')
        email = request.form.get('email')
        payment_method = request.form.get('payment_method', 'cod')
        
        # Get cart items from form
        cart_items_json = request.form.get('cart_items', '[]')
        try:
            cart_items = json.loads(cart_items_json)
            subtotal = float(request.form.get('subtotal', 0))
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing cart items: {str(e)}")
            cart_items = []
            subtotal = 0

        delivery_settings = get_delivery_settings()
        delivery_fee = (
            0.0
            if subtotal >= float(delivery_settings['free_delivery_threshold'])
            else float(delivery_settings['delivery_fee'])
        )
        total = subtotal + delivery_fee
        
        # Store payment method in session for the success page
        session['payment_method'] = payment_method

        # Validate and reserve stock before creating the order.
        stock_reserved = False
        stock_snapshot = None
        stock_ok, stock_message, stock_snapshot = reserve_stock_for_cart_items(cart_items)
        if not stock_ok:
            flash(stock_message, 'error')
            return redirect(url_for('checkout'))
        stock_reserved = True
        
        try:
            # Create order in database
            order = {
                'user_id': session['user_id'],
                'name': name,
                'address': address,
                'city': city,
                'state': state,
                'pincode': pincode,
                'phone': phone,
                'email': email,
                'payment_method': payment_method,
                'status': 'pending',
                'created_at': time.time(),
                'items': cart_items,
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'total': total
            }
            
            # Insert order into database
            order_id = mongo.db.orders.insert_one(order).inserted_id
            
            # Store order ID in session for reference
            session['last_order_id'] = str(order_id)
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('success'))
        except Exception as e:
            if stock_reserved and stock_snapshot is not None:
                try:
                    save_products(stock_snapshot)
                    logger.warning("Stock rollback completed after checkout failure")
                except Exception as rollback_error:
                    logger.error(f"Stock rollback failed: {str(rollback_error)}")
            logger.error(f"Error creating order: {str(e)}")
            flash('There was an error processing your order. Please try again.', 'error')
            
    return render_template('checkout.html', delivery_settings=get_delivery_settings())

@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('success.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Save review to MongoDB
        review = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message
        }
        try:
            mongo.db.reviews.insert_one(review)
        except Exception as e:
            # Optionally log error
            pass

        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get all orders
    orders = list(mongo.db.orders.find().sort('created_at', -1))

    # Set default status for orders if not present
    for order in orders:
        if 'status' not in order:
            order['status'] = 'pending'

    # Get all users
    users = list(mongo.db.users.find())

    # Add customer metrics from order history
    for user in users:
        user_orders = list(
            mongo.db.orders.find({'user_id': str(user['_id'])}).sort('created_at', -1)
        )

        user['order_count'] = len(user_orders)
        user['total_spent'] = sum(float(order.get('total', 0) or 0) for order in user_orders)

        if user_orders:
            latest_order = user_orders[0]
            user['last_order_date'] = latest_order.get('created_at')
            user['phone'] = latest_order.get('phone', 'N/A')
            user['address'] = latest_order.get('address', 'N/A')
            # Requirement: once product is delivered, customer status becomes inactive.
            user['status'] = 'inactive' if latest_order.get('status') == 'delivered' else 'active'
        else:
            user['last_order_date'] = None
            user['phone'] = 'N/A'
            user['address'] = 'N/A'
            user['status'] = 'inactive'

    # Get products for the Products tab
    products = []

    default_products_data = load_products()
    for category, items in default_products_data.items():
        for product in items:
            if isinstance(product, dict):
                p = dict(product)
                p.setdefault('category', category)
                products.append(p)

    try:
        db_products = list(mongo.db.products.find({}, {'_id': 0}))
        products.extend(db_products)
    except Exception as e:
        logger.warning(f"Could not load DB products: {str(e)}")

    low_stock_products = []
    out_of_stock_products = []

    for product in products:
        try:
            stock_value = int(product.get('stock', 0))
        except (TypeError, ValueError):
            continue

        product_info = {
            'id': product.get('id', ''),
            'name': product.get('name', 'Unnamed product'),
            'stock': stock_value
        }

        if stock_value <= 0:
            out_of_stock_products.append(product_info)
        elif stock_value <= LOW_STOCK_THRESHOLD:
            low_stock_products.append(product_info)

    # Get all customer reviews
    reviews = list(mongo.db.reviews.find())
    return render_template(
        'admin.html',
        orders=orders,
        users=users,
        products=products,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        low_stock_threshold=LOW_STOCK_THRESHOLD,
        delivery_settings=get_delivery_settings(),
        reviews=reviews
    )


@app.route('/admin/delivery-settings', methods=['POST'])
@admin_required
def admin_update_delivery_settings():
    try:
        delivery_fee = float(request.form.get('delivery_fee', DEFAULT_DELIVERY_FEE))
        free_delivery_threshold = float(request.form.get('free_delivery_threshold', DEFAULT_FREE_DELIVERY_THRESHOLD))

        if delivery_fee < 0 or free_delivery_threshold < 0:
            flash('Delivery settings must be non-negative values.', 'error')
            return redirect(url_for('admin_dashboard'))

        update_delivery_settings(delivery_fee, free_delivery_threshold)
        flash('Delivery settings updated successfully.', 'success')
    except ValueError:
        flash('Please enter valid numeric values for delivery settings.', 'error')
    except Exception as e:
        logger.error(f"Error updating delivery settings: {str(e)}")
        flash('Failed to update delivery settings.', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<user_id>', methods=['GET'])
@admin_required
def admin_view_user(user_id):
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        orders = list(mongo.db.orders.find({'user_id': str(user['_id'])}).sort('created_at', -1))

        total_spent = sum(float(order.get('total', 0) or 0) for order in orders)
        latest_order = orders[0] if orders else None
        last_order_date = latest_order.get('created_at') if latest_order else None

        if latest_order:
            phone = latest_order.get('phone', 'N/A')
            address = latest_order.get('address', 'N/A')
            status = 'inactive' if latest_order.get('status') == 'delivered' else 'active'
        else:
            phone = 'N/A'
            address = 'N/A'
            status = 'inactive'

        profile = {
            'id': str(user['_id']),
            'username': user.get('username', 'N/A'),
            'email': user.get('email', 'N/A'),
            'phone': phone,
            'address': address,
            'total_orders': len(orders),
            'total_spent': total_spent,
            'last_order': last_order_date,
            'status': status,
        }

        for order in orders:
            order['_id'] = str(order['_id'])

        return render_template('user_profile.html', profile=profile, orders=orders)
    except Exception as e:
        logger.error(f"Error loading user profile: {str(e)}")
        flash('Unable to load user details.', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<user_id>/delete-history', methods=['POST'])
@admin_required
def admin_delete_user_history(user_id):
    try:
        mongo.db.orders.delete_many({'user_id': user_id})
        flash('User history deleted successfully.', 'success')
    except Exception as e:
        logger.error(f"Error deleting user history: {str(e)}")
        flash('Failed to delete user history.', 'error')
    return redirect(url_for('admin_view_user', user_id=user_id))


@app.route('/admin/users/<user_id>/delete-account', methods=['POST'])
@admin_required
def admin_delete_user_account(user_id):
    try:
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        mongo.db.orders.delete_many({'user_id': user_id})
        flash('User account deleted successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        flash('Failed to delete user account.', 'error')
        return redirect(url_for('admin_view_user', user_id=user_id))

@app.route('/api/orders/<order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    try:
        data = request.json
        status = data.get('status')
        
        # Validate status
        valid_statuses = ['pending', 'processing', 'delivered', 'cancelled']
        if not status or status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status value. Must be one of: ' + ', '.join(valid_statuses)}), 400
            
        order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        if order.get('status') == status:
            return jsonify({'success': False, 'message': f'Order is already {status}'}), 400

        result = mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$set': {'status': status}}
        )

        if result.modified_count == 0:
            return jsonify({'success': False, 'message': 'Order status not changed'}), 400

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/orders/<order_id>', methods=['GET'])
@admin_required
def get_order_details(order_id):
    try:
        order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        order['_id'] = str(order['_id'])
        return jsonify(order)
    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/add_product', methods=['POST'])
@admin_required
def add_product():
    try:
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip().lower()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not name or not category:
            flash('Product name and category are required.', 'error')
            return redirect(url_for('admin_dashboard'))

        try:
            price = float(request.form.get('price', 0))
            stock = int(request.form.get('stock', 0))
        except ValueError:
            flash('Invalid price or stock value.', 'error')
            return redirect(url_for('admin_dashboard'))

        if category not in ['vegetables', 'fruits']:
            flash('Category must be vegetables or fruits.', 'error')
            return redirect(url_for('admin_dashboard'))

        image_path = image_url
        image_file = request.files.get('image')

        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                flash('Only JPG, JPEG, PNG and WEBP images are allowed.', 'error')
                return redirect(url_for('admin_dashboard'))

            upload_dir = os.path.join(app.root_path, 'static', 'images', 'Products', category)
            os.makedirs(upload_dir, exist_ok=True)

            saved_name = f"{int(time.time())}_{filename}"
            save_path = os.path.join(upload_dir, saved_name)
            image_file.save(save_path)
            image_path = f"/static/images/Products/{category}/{saved_name}"

        if not image_path:
            image_path = '/static/images/placeholder.jpg'

        products_data = load_products()
        if category not in products_data:
            products_data[category] = []

        product_id = generate_product_id(products_data, category)

        products_data[category].append({
            'id': product_id,
            'name': name,
            'price': price,
            'category': category,
            'image': image_path,
            'description': description,
            'stock': stock
        })

        with open(PRODUCTS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2)

        flash('Product added successfully.', 'success')
    except Exception as e:
        logger.error(f"Error adding product: {str(e)}")
        flash('Failed to add product. Please try again.', 'error')

    return redirect(url_for('admin_dashboard'))

# Create admin user if it doesn't exist
def create_admin_user():
    try:
        # Check if admin user exists
        admin = mongo.db.users.find_one({'email': 'admin@freshmart.com'})
        if not admin:
            # Create admin user
            mongo.db.users.insert_one({
                'username': 'admin',
                'email': 'admin@freshmart.com',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'created_at': time.time()
            })
            logger.info('Admin user created successfully')
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")

# Call create_admin_user within app context
if ensure_mongo_available():
    with app.app_context():
        create_admin_user()

@app.route('/test-image')
def test_image():
    return render_template('test-image.html')

# API endpoint to fetch all products (default + admin-added)
@app.route('/api/products', methods=['GET'])
def api_get_products():
    default_products = []

    default_products_data = load_products()
    for category, items in default_products_data.items():
        for product in items:
            if isinstance(product, dict):
                p = dict(product)
                p.setdefault('category', category)
                default_products.append(p)

    db_products = []
    if ensure_mongo_available():
        try:
            db_products = list(mongo.db.products.find({}, {'_id': 0}))
        except Exception as e:
            logger.warning(f"Could not load DB products: {str(e)}")

    return jsonify(default_products + db_products)

@app.route('/api/products/<product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    try:
        products_data = load_products()
        product_found = False
        
        # Search for and remove the product
        for category, products in products_data.items():
            for i, product in enumerate(products):
                if product['id'] == product_id:
                    products_data[category].pop(i)
                    product_found = True
                    break
            if product_found:
                break
        
        if not product_found:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Save updated products
        with open(PRODUCTS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2)
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    try:
        products_data = load_products()
        for category, products in products_data.items():
            for product in products:
                if product.get('id') == product_id:
                    result = dict(product)
                    result.setdefault('category', category)
                    return jsonify(result)

        return jsonify({'success': False, 'error': 'Product not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    try:
        # Get form data
        data = request.get_json()
        name = data.get('name')
        category = data.get('category')
        price = float(data.get('price'))
        stock = int(data.get('stock'))
        description = data.get('description', '')
        image = data.get('image', '')  # Changed from image_url to image to match frontend
        
        products_data = load_products()
        product_found = False
        old_category = None
        
        # Find the product
        for cat, products in products_data.items():
            for i, product in enumerate(products):
                if product['id'] == product_id:
                    old_category = cat
                    old_index = i
                    product_found = True
                    break
            if product_found:
                break
        
        if not product_found:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Create updated product
        updated_product = {
            'id': product_id,
            'name': name,
            'price': price,
            'category': category,
            'image': image if image else products_data[old_category][old_index]['image'],
            'description': description,
            'stock': stock
        }
        
        # Remove from old category if category changed
        if old_category != category:
            products_data[old_category].pop(old_index)
            
            # Ensure new category exists
            if category not in products_data:
                products_data[category] = []
                
            # Add to new category
            products_data[category].append(updated_product)
        else:
            # Update in same category
            products_data[category][old_index] = updated_product
        
        # Save updated products
        with open(PRODUCTS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2)
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Add host='0.0.0.0' to make the server publicly available
    app.run(debug=True, host='0.0.0.0', port=5000)
