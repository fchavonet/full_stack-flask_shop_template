from flask import Flask, render_template
from flask_login import current_user, LoginManager, login_required

from auth import auth_bp
from config import Config
from models import db, User


def create_app() -> Flask:
    """
    Build and return the Flask app.
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
        return render_template("admin/dashboard.html")

    @app.cli.command("init-db")
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
