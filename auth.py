import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user

from models import db, User

# Create blueprint.
auth_bp = Blueprint("auth", __name__)

# Require one uppercase and at least eight chars.
PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z]).{8,}$")


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

        # Require all fields.
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        # Check password format.
        if not PASSWORD_PATTERN.match(password):
            flash("Password must be at least 8 characters long and contain at least one uppercase letter.", "danger",)
            return redirect(url_for("auth.register"))

        # Check duplicates.
        existing = User.query.filter(
            (User.username == username) | (User.email == email)).first()
        if existing:
            flash("User already exists.", "warning")
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
    flash("Logged out.", "info")
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
            duplicate = User.query.filter(((User.username == new_username) | (
                User.email == new_email)) & (User.id != current_user.id)).first()
            if duplicate:
                flash("Username or email already taken.", "warning")
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

    # Render profile page.
    return render_template("auth/profile.html", title="Profile")
