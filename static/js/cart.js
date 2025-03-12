class Cart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('cart')) || [];
        this.updateUI();
    }

    addItem(product) {
        try {
            console.log('Adding product to cart:', product);
            const existingItem = this.items.find(item => item.id === product.id);
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                this.items.push({ ...product, quantity: 1 });
            }
            this.save();
            this.updateUI();
            // Show feedback to user
            const toast = document.createElement('div');
            toast.className = 'alert alert-success position-fixed bottom-0 end-0 m-3';
            toast.innerHTML = `
                <div class="d-flex align-items-center">
                    <span>${product.name} added to cart</span>
                    <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        } catch (error) {
            console.error('Error adding item to cart:', error);
            const toast = document.createElement('div');
            toast.className = 'alert alert-danger position-fixed bottom-0 end-0 m-3';
            toast.innerHTML = `
                <div class="d-flex align-items-center">
                    <span>Error adding item to cart</span>
                    <button type="button" class="btn-close ms-3" data-bs-dismiss="alert"></button>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    }

    removeItem(productId) {
        this.items = this.items.filter(item => item.id !== productId);
        this.save();
        this.updateUI();
    }

    updateQuantity(productId, quantity) {
        const item = this.items.find(item => item.id === productId);
        if (item) {
            item.quantity = parseInt(quantity);
            if (item.quantity <= 0) {
                this.removeItem(productId);
            }
        }
        this.save();
        this.updateUI();
    }

    getTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
    }

    save() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    }

    updateUI() {
        const cartCount = document.getElementById('cart-count');
        const cartTotal = document.getElementById('cart-total');
        const cartItems = document.getElementById('cart-items');

        if (cartCount) {
            cartCount.textContent = this.items.reduce((total, item) => total + item.quantity, 0);
        }

        if (cartTotal) {
            cartTotal.textContent = `$${this.getTotal()}`;
        }

        if (cartItems) {
            cartItems.innerHTML = this.items.map(item => `
                <div class="cart-item card mb-3">
                    <div class="row g-0">
                        <div class="col-md-4">
                            <img src="${item.image}" class="img-fluid rounded-start" alt="${item.name}">
                        </div>
                        <div class="col-md-8">
                            <div class="card-body">
                                <h5 class="card-title">${item.name}</h5>
                                <p class="card-text">Price: $${item.price}</p>
                                <div class="quantity-controls">
                                    <button class="btn btn-sm btn-secondary" onclick="cart.updateQuantity('${item.id}', ${item.quantity - 1})">-</button>
                                    <span class="mx-2">${item.quantity}</span>
                                    <button class="btn btn-sm btn-secondary" onclick="cart.updateQuantity('${item.id}', ${item.quantity + 1})">+</button>
                                </div>
                                <button class="btn btn-danger btn-sm mt-2" onclick="cart.removeItem('${item.id}')">Remove</button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }
}

const cart = new Cart();