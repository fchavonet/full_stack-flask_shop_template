import os
from flask import Flask, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, LoginManager, login_required
from werkzeug.utils import secure_filename

from auth import auth_bp
from config import Config
from models import db, Order, OrderItem, Product, User
from sqlalchemy import func
from urllib.parse import urlparse


def allowed_file(filename: str) -> bool:
    """
    Check if filename extension is allowed.
    """

    # Return True if filename has an allowed extension.
    return ("." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["IMAGE_EXTENSIONS"])


def get_cart():
    """
    Retrieve shopping cart from session.
    """

    # Return cart or empty dict if not set.
    return session.get("cart", {})


def save_cart(cart):
    """
    Save shopping cart to session.
    """

    # Store cart in session and mark modified.
    session["cart"] = cart
    session.modified = True


def create_app() -> Flask:
    """
    Build and return the Flask application.
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database.
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    # Load user by ID.
    @login_manager.user_loader
    def load_user(user_id: str):
        """
        Return a user instance by ID.
        """

        return User.query.get(int(user_id))

    # Register authentication blueprint.
    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        """
        Render home page.
        """

        return render_template("main/index.html", title="Home")

    @app.context_processor
    def inject_products():
        """
        Injects the latest and top-selling products into the template context.
        """

        latest_products = (
            Product.query
            .order_by(Product.id.desc())
            .limit(4)
            .all()
        )

        top_query = (
            db.session
            .query(Product, func.sum(OrderItem.quantity).label("total"))
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(4)
            .all()
        )
        top_products = [p for p, _ in top_query]

        return dict(latest_products=latest_products, top_products=top_products)

    @app.route("/about")
    def about():
        """
        Render about page.
        """

        # Render about template.
        return render_template("main/about.html", title="About")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """
        Render admin dashboard.
        """

        if not current_user.is_admin:
            return render_template("error/403.html"), 403
        products = Product.query.all()
        return render_template("admin/dashboard.html", title="Dashboard", products=products)

    @app.route("/dashboard/add-product", methods=["GET", "POST"])
    @login_required
    def add_product():
        """
        Add a new product.
        """

        if not current_user.is_admin:
            return render_template("error/403.html"), 403

        if request.method == "POST":
            # Get form fields.
            title = request.form["title"]
            description = request.form["description"]
            price = float(request.form["price"])
            quantity = int(request.form["quantity"])
            image_file = request.files["image"]

            # Ensure upload folder exists.
            upload_folder = current_app.config["PRODUCT_PICTURE_FOLDER"]
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Save uploaded image or use default.
            if image_file and image_file.filename != "" and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
            else:
                filename = current_app.config["DEFAULT_PRODUCT_PICTURE"]

            # Create and commit product record.
            product = Product(
                title=title,
                description=description,
                image=filename,
                price=price,
                quantity=quantity
            )
            db.session.add(product)
            db.session.commit()
            flash("Product added successfully.", "success")
            return redirect(url_for("dashboard"))

        # Render add-product form.
        return render_template("admin/add_product.html")

    @app.route("/dashboard/delete-product/<int:product_id>", methods=["POST"])
    @login_required
    def delete_product(product_id):
        """
        Delete a product and its image.
        """

        if not current_user.is_admin:
            return render_template("error/403.html"), 403

        product = Product.query.get_or_404(product_id)

        # Remove image file if not default.
        default_image = current_app.config["DEFAULT_PRODUCT_PICTURE"]
        if product.image != default_image:
            image_path = os.path.join(current_app.config["PRODUCT_PICTURE_FOLDER"], product.image)

            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete product record.
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully.", "warning")
        return redirect(url_for("dashboard"))

    @app.route("/dashboard/edit-product/<int:product_id>", methods=["GET", "POST"])
    @login_required
    def edit_product(product_id):
        """
        Edit an existing product.
        """

        if not current_user.is_admin:
            return render_template("error/403.html"), 403

        product = Product.query.get_or_404(product_id)

        if request.method == "POST":
            # Update basic fields.
            product.title = request.form["title"]
            product.description = request.form["description"]
            product.price = float(request.form["price"])
            product.quantity = int(request.form["quantity"])

            # Ensure upload folder exists.
            upload_folder = current_app.config["PRODUCT_PICTURE_FOLDER"]

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            image_file = request.files["image"]
            # Handle image replacement if provided.
            if image_file and image_file.filename != "" and allowed_file(image_file.filename):
                # Remove old image if not default.
                old_image = os.path.join(upload_folder, product.image)

                if (product.image != current_app.config["DEFAULT_PRODUCT_PICTURE"] and os.path.exists(old_image)):
                    os.remove(old_image)

                # Save new image.
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
                product.image = filename

            # Commit changes to database.
            db.session.commit()
            flash("Product updated.", "success")
            return redirect(url_for("dashboard"))

        # Render edit-product form.
        return render_template("admin/edit_product.html", product=product)

    @app.route("/catalog")
    def catalog():
        """
        List all products with optional sorting and pagination.
        """

        sort_by = request.args.get("sort_by", "title")
        page = request.args.get("page", 1, type=int)
        per_page = 12

        query = Product.query

        if sort_by == "price_asc": query = query.order_by(Product.price.asc())
        elif sort_by == "price_desc": query = query.order_by(Product.price.desc())
        elif sort_by == "quantity_asc": query = query.order_by(Product.quantity.asc())
        elif sort_by == "quantity_desc": query = query.order_by(Product.quantity.desc())
        else: query = query.order_by(Product.title.asc())

        products = query.paginate(page=page, per_page=per_page)

        return render_template("shop/catalog.html", title="Catalog", products=products, sort_by=sort_by)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        """
        Show product details.
        """

        product = Product.query.get_or_404(product_id)
        return render_template("shop/product_detail.html", product=product)

    @app.route("/add-to-cart/<int:product_id>", methods=["POST"])
    @login_required
    def add_to_cart(product_id):
        """
        Add item to shopping cart.
        """

        # Retrieve product or 404.
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get("quantity", 1))

        next_page = request.form.get("next") or request.referrer or url_for("catalog")
        if urlparse(next_page).netloc: next_page = url_for("catalog")

        # Validate quantity.
        if quantity <= 0:
            flash("Invalid quantity.", "danger")
            return redirect(next_page)

        # Get current cart.
        cart = get_cart()

        key = str(product_id)
        current_quantity = cart.get(key, 0)

        # Check stock availability.
        if current_quantity + quantity > product.quantity:
            flash("Not enough stock available.", "danger")
            return redirect(next_page)

        # Update cart and save.
        cart[key] = current_quantity + quantity
        save_cart(cart)

        flash("Product added to cart.", "success")
        return redirect(next_page)

    @app.context_processor
    def inject_cart_quantity():
        """
        Inject total cart item count into template context.
        """

        cart = get_cart()
        quantity = sum(cart.values()) if cart else 0
        return dict(cart_quantity=quantity)

    @app.route("/cart")
    @login_required
    def cart():
        """
        Display shopping cart contents.
        """

        cart = get_cart()
        items = []
        total = 0

        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                # Calculate subtotal and add to total.
                subtotal = product.price * quantity
                total += subtotal
                items.append({
                    "product": product,
                    "quantity": quantity,
                    "subtotal": subtotal
                })

        # Render cart template with items and total.
        return render_template("shop/cart.html", title="Cart", items=items, total=total)

    @app.route("/remove-from-cart/<int:product_id>", methods=["POST"])
    @login_required
    def remove_from_cart(product_id):
        """
        Remove item from shopping cart.
        """

        cart = get_cart()
        product_id_str = str(product_id)

        if product_id_str in cart:
            # Remove item and save cart.
            del cart[product_id_str]
            save_cart(cart)
            flash("Item removed from cart.", "warning")
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["POST"])
    @login_required
    def checkout():
        """
        Process checkout and create order.
        """

        cart = get_cart()

        # Ensure cart is not empty.
        if not cart:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        # Create order record.
        order = Order(user_id=current_user.id)
        db.session.add(order)

        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))

            # Validate stock per item.
            if not product or product.quantity < quantity:
                flash("Not enough stock.", "danger")
                return redirect(url_for("cart"))

            # Decrease product stock.
            product.quantity -= quantity

            # Create order item record.
            order_item = OrderItem(
                order=order,
                product_id=product.id,
                quantity=quantity,
                product_title=product.title,
                product_price=product.price
            )
            db.session.add(order_item)

        # Commit all changes and clear cart.
        db.session.commit()
        session.pop("cart", None)
        flash("Order placed successfully!", "success")
        return redirect(url_for("order_history"))

    @app.route("/orders")
    @login_required
    def order_history():
        """
        Show user's past orders.
        """

        # Retrieve orders sorted by creation date.
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("shop/orders.html", orders=orders)

    @app.route("/terms_of_use")
    def terms_of_use():
        """
        Render terms of use page.
        """

        # Render terms of use template.
        return render_template("policies/terms_of_use.html", title="Terms of Use")

    @app.route("/legals")
    def legals():
        """
        Render legals page.
        """

        # Render legals template.
        return render_template("policies/legals.html", title="Legals")

    @app.cli.command("init-database")
    def init_db():
        """
        Create database tables.
        """

        with app.app_context():
            db.create_all()
            print("Database initialized.")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
