from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    """

    # Primary key for the user record.
    id = db.Column(db.Integer, primary_key=True)
    # Unique username for login.
    username = db.Column(db.String(64), unique=True, nullable=False)
    # Unique email address for contact.
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Hashed password for security.
    password_hash = db.Column(db.String(256), nullable=False)
    # Flag indicating if user has admin rights.
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password: str) -> None:
        """
        Hash and store the user password.
        """

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches stored hash.
        """

        return check_password_hash(self.password_hash, password)
