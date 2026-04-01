from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('page.student_dashboard'))
        return redirect(url_for('page.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            if user.role == 'student':
                return redirect(next_page or url_for('page.student_dashboard'))
            return redirect(next_page or url_for('page.dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('page.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        
        # Verify admin secret key if role is admin
        if role == 'admin':
            admin_secret = request.form.get('admin_secret')
            if admin_secret != 'HOSTELADMIN2024':
                flash('Invalid Administrator Secret Key.', 'danger')
                return redirect(url_for('auth.signup'))
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email address already exists', 'danger')
            return redirect(url_for('auth.signup'))
            
        new_user = User(name=name, email=email, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    verified_email = None

    if request.method == 'POST':
        step = request.form.get('step')

        # Step 1 — verify the email exists
        if step == 'verify_email':
            email = request.form.get('email', '').strip()
            user = User.query.filter_by(email=email).first()
            if user:
                # Email found — show the reset form with the verified email
                verified_email = email
            else:
                flash('No account found with that email address.', 'danger')

        # Step 2 — reset the password
        elif step == 'reset_password':
            email = request.form.get('email', '').strip()
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if new_password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
                verified_email = email  # keep the user on step 2
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                verified_email = email
            else:
                user = User.query.filter_by(email=email).first()
                if user:
                    user.set_password(new_password)
                    db.session.commit()
                    flash('Password reset successfully! You can now log in.', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('Something went wrong. Please start over.', 'danger')

    return render_template('forgot_password.html', verified_email=verified_email)
