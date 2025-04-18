import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Base config for Flask application.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-this-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Images upload configuration.
    IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

    # Profile pictures.
    PROFILE_PICTURE_FOLDER = os.path.join(basedir, "static", "images", "profile_pictures")
    DEFAULT_PROFILE_PICTURE = "default_profile.webp"

    # Product pictures.
    PRODUCT_PICTURE_FOLDER = os.path.join(basedir, "static", "images", "product_pictures")
    DEFAULT_PRODUCT_PICTURE = "default_product.webp"
