import os
import re
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.utils import secure_filename

from app.models import db, User

# Create blueprint.
auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

# Require one uppercase and at least eight chars.
PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z]).{8,}$")


def allowed_file(filename: str) -> bool:
    """
    Check if filename extension is allowed.
    """
    return ("." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["IMAGE_EXTENSIONS"])


# REGISTER
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.
    """

    # Redirect if user already signed in.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard" if current_user.is_admin else "index"))

    if request.method == "POST":
        # Get form data.
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Require all fields.
        if not username or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        # Check if passwords match.
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        # Check password format.
        if not PASSWORD_PATTERN.match(password):
            flash("Password must be at least 8 characters long and contain at least one uppercase letter.", "danger")
            return redirect(url_for("auth.register"))

        # Check duplicates.
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash("User already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Create user.
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful.", "success")
        return redirect(url_for("auth.login"))

    # Render register page.
    return render_template("auth/register.html", title="Register")


# LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.
    """

    # Redirect if user already signed in.
    if current_user.is_authenticated:
        return redirect(url_for("dashboard" if current_user.is_admin else "index"))

    if request.method == "POST":
        # Get form data.
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user and validate password.
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard" if user.is_admin else "index"))

        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login"))

    # Render login page.
    return render_template("auth/login.html", title="Login")


# LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    """
    Log out current user.
    """

    logout_user()
    flash("Logged out.", "warning")
    return redirect(url_for("index"))


# PROFILE
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """
    Display and update user profile.
    """

    if request.method == "POST":
        # Determine which form was submitted.
        form_type = request.form.get("form_type")

        if form_type == "info":
            # Update username and email.
            new_username = request.form.get("username")
            new_email = request.form.get("email")

            # Require both fields.
            if not new_username or not new_email:
                flash("Both username and email are required.", "danger")
                return redirect(url_for("auth.profile"))

            # Check for duplicates.
            duplicate = User.query.filter(((User.username == new_username) | (User.email == new_email)) & (User.id != current_user.id)).first()
            if duplicate:
                flash("Username or email already taken.", "danger")
                return redirect(url_for("auth.profile"))

            current_user.username = new_username
            current_user.email = new_email
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("auth.profile"))

        if form_type == "password":
            # Update password.
            new_password = request.form.get("password")
            if not PASSWORD_PATTERN.match(new_password):
                flash("Password must be at least 8 characters long and contain at least one uppercase letter.", "danger")
                return redirect(url_for("auth.profile"))

            current_user.set_password(new_password)
            db.session.commit()
            flash("Password changed.", "success")
            return redirect(url_for("auth.profile"))

        if form_type == "picture":
            # Handle profile picture upload.
            if "picture" not in request.files:
                flash("No file part.", "danger")
                return redirect(url_for("auth.profile"))

            file = request.files["picture"]

            # Flash if no file was selected.
            if file.filename == "":
                flash("No selected file.", "danger")
                return redirect(url_for("auth.profile"))

            # Flash if file extension is not allowed.
            if not allowed_file(file.filename):
                flash("File type not allowed.", "danger")
                return redirect(url_for("auth.profile"))

            profile_picture_folder = current_app.config["PROFILE_PICTURE_FOLDER"]
            if not os.path.exists(profile_picture_folder):
                os.makedirs(profile_picture_folder)

            # Remove old picture if it is not the default.
            old_filename = current_user.profile_picture
            default_pic = current_app.config["DEFAULT_PROFILE_PICTURE"]
            if old_filename != default_pic:
                old_path = os.path.join(profile_picture_folder, old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Save new picture file.
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(f"user_{current_user.id}.{ext}")
            upload_path = os.path.join(profile_picture_folder, filename)
            file.save(upload_path)

            # Update user record with new picture.
            current_user.profile_picture = filename
            db.session.commit()
            flash("Profile picture updated.", "success")
            return redirect(url_for("auth.profile"))

    # Render profile page.
    return render_template("auth/profile.html", title="Profile")
