import os
from flask import Flask, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, LoginManager, login_required
from werkzeug.utils import secure_filename

from auth import auth_bp
from config import Config
from models import db, Product, User


def allowed_file(filename: str) -> bool:
    """
    Check if filename extension is allowed.
    """

    # Return True if filename has an allowed extension.
    return ("." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["IMAGE_EXTENSIONS"])


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

        return render_template("index.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """
        Render admin dashboard.
        """

        if not current_user.is_admin:
            return render_template("403.html"), 403
        products = Product.query.all()
        return render_template("admin/dashboard.html", products=products)

    @app.route("/dashboard/add-product", methods=["GET", "POST"])
    @login_required
    def add_product():
        """
        Add a new product.
        """

        if not current_user.is_admin:
            return render_template("403.html"), 403

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
            return render_template("403.html"), 403

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
        flash("Product and its image deleted successfully.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/dashboard/edit-product/<int:product_id>", methods=["GET", "POST"])
    @login_required
    def edit_product(product_id):
        """
        Edit an existing product.
        """

        if not current_user.is_admin:
            return render_template("403.html"), 403

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
        List all products.
        """

        products = Product.query.all()
        return render_template("catalog.html", products=products)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        """
        Show product details.
        """

        product = Product.query.get_or_404(product_id)
        return render_template("product_detail.html", product=product)

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
