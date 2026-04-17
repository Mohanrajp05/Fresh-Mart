class Cart {
    constructor() {
        console.log('Initializing cart...');
        this.items = [];
        
        // Check login status
        const isLoggedIn = document.body.dataset.userLoggedIn === 'true';
        
        if (!isLoggedIn) {
            // Clear cart if user is not logged in
            this.clearCart();
        } else {
            try {
                const savedCart = localStorage.getItem('cart');
                if (savedCart) {
                    this.items = JSON.parse(savedCart);
                    console.log('Loaded saved cart:', this.items);
                }
            } catch (error) {
                console.error('Error loading cart from localStorage:', error);
            }
        }
        this.updateUI();
    }

    updateCartCount() {
        const cartCountElements = document.querySelectorAll('.cart-count');
        const totalItems = this.items.reduce((total, item) => total + item.quantity, 0);
        
        cartCountElements.forEach(element => {
            element.textContent = totalItems;
            // Show/hide the badge based on count
            if (totalItems > 0) {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        });
    }

    addItem(product) {
        try {
            console.log('Adding product to cart:', product);
            if (!product || !product.id) {
                console.error('Invalid product:', product);
                return;
            }

            // Block only the selected product when it is out of stock.
            if (parseInt(product.stock || 0, 10) <= 0) {
                const toast = document.createElement('div');
                toast.className = 'alert alert-danger position-fixed bottom-0 end-0 m-3';
                toast.style.zIndex = '1050';
                toast.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span>${product.name} is out of stock.</span>
                        <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                    </div>
                `;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                return;
            }

            // Check if user is logged in
            const isLoggedIn = document.body.dataset.userLoggedIn === 'true';
            
            if (!isLoggedIn) {
                // Show login required message
                const toast = document.createElement('div');
                toast.className = 'alert alert-warning position-fixed bottom-0 end-0 m-3';
                toast.style.zIndex = '1050';
                toast.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span>Please <a href="/login" class="alert-link" style="color: #2ecc71; text-decoration: none;">login</a> to add items to your cart.</span>
                        <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                    </div>
                `;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
                return; // Exit the function without adding to cart
            }
            
            const existingItem = this.items.find(item => item.id === product.id);
            if (existingItem) {
                // Check if adding one more would exceed the limit of 10
                if (existingItem.quantity >= 10) {
                    // Show limit reached message
                    const toast = document.createElement('div');
                    toast.className = 'alert alert-warning position-fixed bottom-0 end-0 m-3';
                    toast.style.zIndex = '1050';
                    toast.innerHTML = `
                        <div class="d-flex align-items-center">
                            <span>Maximum limit of 10 items reached for ${product.name}</span>
                            <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                    return;
                }
                existingItem.quantity += 1;
                console.log('Updated quantity for existing item:', existingItem);
            } else {
                // Store complete product information
                this.items.push({
                    id: product.id,
                    name: product.name,
                    price: product.price,
                    image: product.image,
                    quantity: 1
                });
                console.log('Added new item to cart');
            }
            this.save();
            this.updateUI();
            this.updateCartCount();

            // Show success message
            const toast = document.createElement('div');
            toast.className = 'alert alert-success position-fixed bottom-0 end-0 m-3';
            toast.style.zIndex = '1050';
            toast.innerHTML = `
                <div class="d-flex align-items-center">
                    <span>Item added to cart successfully!</span>
                    <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);

        } catch (error) {
            console.error('Error adding item to cart:', error);
        }
    }

    updateQuantity(productId, newQuantity) {
        try {
            if (newQuantity <= 0) {
                this.removeItem(productId);
            } else if (newQuantity > 10) {
                // Show limit exceeded message
                const toast = document.createElement('div');
                toast.className = 'alert alert-warning position-fixed bottom-0 end-0 m-3';
                toast.style.zIndex = '1050';
                toast.innerHTML = `
                    <div class="d-flex align-items-center">
                        <span>Maximum limit is 10 items per product</span>
                        <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                    </div>
                `;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            } else {
                const item = this.items.find(item => item.id === productId);
                if (item) {
                    item.quantity = newQuantity;
                    this.save();
                    this.updateUI();
                    this.updateCartCount();
                }
            }
        } catch (error) {
            console.error('Error updating quantity:', error);
        }
    }

    removeItem(productId) {
        try {
            this.items = this.items.filter(item => item.id !== productId);
            this.save();
            this.updateUI();
            this.updateCartCount();
        } catch (error) {
            console.error('Error removing item:', error);
        }
    }

    clearCart() {
        try {
            this.items = [];
            localStorage.removeItem('cart');
            this.updateUI();
            this.updateCartCount();
        } catch (error) {
            console.error('Error clearing cart:', error);
        }
    }

    save() {
        try {
            localStorage.setItem('cart', JSON.stringify(this.items));
        } catch (error) {
            console.error('Error saving cart to localStorage:', error);
        }
    }

    updateUI() {
        try {
            const cartItems = document.querySelector('.cart-items');
            const cartTotal = document.querySelector('.cart-total');
            
            if (!cartItems) return;
            
            if (this.items.length === 0) {
                cartItems.innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-cart-x" style="font-size: 3rem;"></i>
                        <p class="mt-3">Your cart is empty</p>
                    </div>
                `;
                if (cartTotal) cartTotal.textContent = '₹0.00';
            } else {
                cartItems.innerHTML = this.items.map(item => {
                    const name = item.name || 'Product Name Not Available';
                    const price = item.price || 0;
                    const image = item.image || '/static/images/placeholder.jpg';
                    const quantity = item.quantity || 0;
                    const subtotal = (price * quantity).toFixed(2);

                    return `
                        <div class="card mb-3">
                            <div class="row g-0">
                                <div class="col-md-4">
                                    <img src="${image}" 
                                         class="img-fluid rounded-start" 
                                         alt="${name}"
                                         onerror="this.src='/static/images/placeholder.jpg'"
                                         style="max-height: 200px; width: 100%; object-fit: cover;">
                                </div>
                                <div class="col-md-8">
                                    <div class="card-body">
                                        <h5 class="card-title">${name}</h5>
                                        <p class="card-text">Price: ₹${price}</p>
                                        <div class="d-flex align-items-center gap-2 mb-2">
                                            <button class="btn btn-secondary btn-sm" 
                                                    onclick="cart.updateQuantity('${item.id}', ${quantity - 1})"
                                                    ${quantity <= 1 ? 'disabled' : ''}>-</button>
                                            <span class="mx-2">${quantity}</span>
                                            <button class="btn btn-secondary btn-sm" 
                                                    onclick="cart.updateQuantity('${item.id}', ${quantity + 1})">+</button>
                                        </div>
                                        <p class="card-text">Subtotal: ₹${subtotal}</p>
                                        <button class="btn btn-success btn-sm" 
                                                onclick="cart.removeItem('${item.id}')">Remove</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');

                if (cartTotal) {
                    const total = this.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
                    cartTotal.textContent = `₹${total.toFixed(2)}`;
                }
            }
            
            // Update cart count
            this.updateCartCount();
            
        } catch (error) {
            console.error('Error updating UI:', error);
        }
    }
}

// Initialize cart
const cart = new Cart();

// Product data moved to product.js. Please reference products from product.js.

// Function to render products dynamically from API
function renderProducts() {
    const productContainer = document.querySelector('.row.g-4');
    if (!productContainer) return;
    productContainer.innerHTML = '';

    fetch('/api/products')
        .then(response => response.json())
        .then(products => {
            // Group products by category
            const grouped = {};
            products.forEach(product => {
                if (!grouped[product.category]) grouped[product.category] = [];
                grouped[product.category].push(product);
            });
            for (const category in grouped) {
                grouped[category].forEach(product => {
                    const stock = parseInt(product.stock || 0, 10);
                    const isOutOfStock = stock <= 0;
                    const productCard = document.createElement('div');
                    productCard.className = 'col-md-4 col-lg-3 product-card';
                    productCard.setAttribute('data-category', category);
                    productCard.innerHTML = `
                        <div class="card h-100">
                            <img src="${product.image}" class="card-img-top product-image" alt="${product.name}"
                                 style="height: 200px; object-fit: cover;">
                            <div class="card-body">
                                <h5 class="card-title">${product.name}</h5>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="h5 mb-0">₹${product.price}</span>
                                    <button class="btn ${isOutOfStock ? 'btn-secondary' : 'btn-primary'} add-to-cart" 
                                            data-id="${product.id}"
                                            data-name="${product.name}"
                                            data-price="${product.price}"
                                            data-image="${product.image}"
                                            data-stock="${stock}"
                                            ${isOutOfStock ? 'aria-disabled="true" style="opacity:0.7;cursor:not-allowed;" title="Out of Stock"' : ''}>
                                        ${isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    productContainer.appendChild(productCard);
                });
            }
            // Add click event listeners to Add to Cart buttons
            document.querySelectorAll('.add-to-cart').forEach(button => {
                button.addEventListener('click', function() {
                    const productData = {
                        id: this.dataset.id,
                        name: this.dataset.name,
                        price: parseFloat(this.dataset.price),
                        image: this.dataset.image,
                        stock: parseInt(this.dataset.stock || 0, 10)
                    };
                    cart.addItem(productData);
                });
            });
        })
        .catch(error => {
            productContainer.innerHTML = '<div class="alert alert-danger">Failed to load products.</div>';
            console.error('Error fetching products:', error);
        });
}

// Call renderProducts on page load
document.addEventListener('DOMContentLoaded', function() {
    // Render products
    renderProducts();
    
    // Add event listeners for category filters
    const categoryFilters = document.querySelectorAll('.category-filter');
    categoryFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            
            // Update active button
            categoryFilters.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter products
            const productCards = document.querySelectorAll('.product-card');
            productCards.forEach(card => {
                if (category === 'all' || card.getAttribute('data-category') === category) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
    
    // Add event listener for search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const productCards = document.querySelectorAll('.product-card');
            
            productCards.forEach(card => {
                const productName = card.querySelector('.card-title').textContent.toLowerCase();
                if (productName.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});