import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Base config for Flask application.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-this-in-production"
    SQLALCHEMY_DATABASE_URI = (os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Profile picture upload.
    UPLOAD_FOLDER = os.path.join(basedir, "static", "images/profile_pictures")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Default picture filename
    DEFAULT_PROFILE_PICTURE = "default.webp"
