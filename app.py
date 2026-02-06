from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import secrets
import hashlib
from functools import wraps
import os
import logging
import boto3
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Attr

# Load environment variables from .env file (for local development only)
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
app.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Secure session configuration
app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME', 'stocker_session')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = os.getenv('REMEMBER_COOKIE_SAMESITE', 'Lax')
app.config['REMEMBER_COOKIE_SECURE'] = os.getenv('REMEMBER_COOKIE_SECURE', 'true').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    minutes=int(os.getenv('SESSION_LIFETIME_MINUTES', '30'))
)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(
    days=int(os.getenv('REMEMBER_ME_DAYS', '14'))
)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)

# DynamoDB Tables
users_table = dynamodb.Table(os.getenv('DYNAMODB_USERS_TABLE', 'stocker-users'))
portfolios_table = dynamodb.Table(os.getenv('DYNAMODB_PORTFOLIOS_TABLE', 'stocker-portfolios'))
transactions_table = dynamodb.Table(os.getenv('DYNAMODB_TRANSACTIONS_TABLE', 'stocker-transactions'))

# SNS Configuration
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def _send_email_via_sns(subject, message):
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not configured. Email content: %s | %s", subject, message)
        return
    try:
        sns_client.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
    except Exception as e:
        logger.error(f"SNS publish error: {str(e)}")

# CSRF protection for all forms
csrf = CSRFProtect(app)

# Login manager configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'
login_manager.session_protection = 'strong'


class User(UserMixin):
    def __init__(self, email, user_id, name, role='user', status='active'):
        self.id = email
        self.user_id = user_id
        self.name = name
        self.role = role or 'user'
        self.status = status or 'active'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_active(self):
        return self.status == 'active'


def _get_user_by_email(email):
    try:
        response = users_table.get_item(Key={'email': email})
        user = response.get('Item')
        if not user:
            return None
        return User(
            email=user.get('email'),
            user_id=user.get('user_id'),
            name=user.get('name'),
            role=user.get('role', 'user'),
            status=user.get('status', 'active')
        )
    except Exception as e:
        logger.error(f"User lookup error: {str(e)}")
        return None


@login_manager.user_loader
def load_user(user_id):
    return _get_user_by_email(user_id)

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        if not current_user.is_admin:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard'))

        return f(*args, **kwargs)
    return decorated_function

# Landing Page
@app.route('/')
def index():
    return render_template('index.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        try:
            # Query user from DynamoDB
            response = users_table.get_item(Key={'email': email})
            user = response.get('Item')
            
            if user:
                if user.get('status', 'active') != 'active':
                    flash('Account is inactive. Contact support.', 'error')
                    return render_template('login.html')

                if not user.get('email_verified', False):
                    flash('Please verify your email before logging in.', 'error')
                    return render_template('login.html')

                password_hash = user.get('password_hash')
                if password_hash:
                    if not check_password_hash(password_hash, password):
                        flash('Invalid email or password', 'error')
                        logger.warning(f"Failed login attempt for: {email}")
                        return render_template('login.html')
                else:
                    # Legacy plaintext support (migrate on next successful login)
                    legacy_password = user.get('password')
                    if not legacy_password or legacy_password != password:
                        flash('Invalid email or password', 'error')
                        logger.warning(f"Failed login attempt for: {email}")
                        return render_template('login.html')

                    new_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
                    users_table.update_item(
                        Key={'email': email},
                        UpdateExpression="SET password_hash=:ph, updated_at=:ua REMOVE password",
                        ExpressionAttributeValues={
                            ':ph': new_hash,
                            ':ua': datetime.utcnow().isoformat()
                        }
                    )

                session.clear()
                session.permanent = True
                user_obj = User(
                    email=user.get('email'),
                    user_id=user.get('user_id'),
                    name=user.get('name'),
                    role=user.get('role', 'user'),
                    status=user.get('status', 'active')
                )
                login_user(user_obj, remember=remember)
                logger.info(f"User logged in: {email} (Role: {user.get('role')})")
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
                logger.warning(f"Failed login attempt for: {email}")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('fullname')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')

        if len(password or '') < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('signup.html')
        
        try:
            # Check if user exists
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                flash('Email already registered', 'error')
                return render_template('signup.html')
            
            # Create new user in DynamoDB
            user_id = f"user#{int(os.urandom(4).hex(), 16)}"
            password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            verification_token = secrets.token_urlsafe(32)
            verification_token_hash = _hash_token(verification_token)
            verification_sent_at = datetime.utcnow().isoformat()
            logger.info(f"Generated verification token for {email}: {verification_token}")
            logger.info(f"Token hash to store: {verification_token_hash}")
            users_table.put_item(Item={
                'email': email,
                'user_id': user_id,
                'name': name,
                'password_hash': password_hash,
                'role': 'user',  # New users are always 'user' role
                'status': 'active',
                'email_verified': False,
                'email_verification_token_hash': verification_token_hash,
                'email_verification_sent_at': verification_sent_at,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
            
            # Send welcome notification via SNS
            if SNS_TOPIC_ARN:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject='Welcome to Stocker',
                    Message=f'Welcome {name}! Your account has been created.'
                )

            verify_link = url_for('verify_email', token=verification_token, _external=True)
            _send_email_via_sns(
                'Verify your Stocker email',
                f"Hi {name},\n\nPlease verify your email by clicking the link below:\n{verify_link}\n\nIf you did not create this account, you can ignore this email."
            )
            
            logger.info(f"New user registered: {email}")
            flash('Account created successfully. Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            flash('An error occurred during signup', 'error')
    
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        try:
            # Send notification via SNS
            if SNS_TOPIC_ARN:
                contact_message = f"""
New Contact Form Submission
---------------------------
Name: {first_name} {last_name}
Email: {email}
Subject: {subject}
Message: {message}
"""
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject=f'Contact Form: {subject}',
                    Message=contact_message
                )
            
            logger.info(f"Contact form submitted by {email} - Subject: {subject}")
            flash('Thank you for contacting us. We will respond within 24 hours.', 'success')
        except Exception as e:
            logger.error(f"Contact form error: {str(e)}")
            flash('Message received. We will get back to you soon.', 'success')
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))


@app.route('/verify-email')
def verify_email():
    token = request.args.get('token')
    if not token:
        flash('Invalid verification link', 'error')
        return redirect(url_for('login'))

    token_hash = _hash_token(token)
    logger.info(f"Verification attempt - Token: {token}")
    logger.info(f"Verification attempt - Token hash: {token_hash}")
    try:
        # Scan is avoided; rely on direct lookup with token hash (requires token hash stored on user item)
        response = users_table.scan(
            FilterExpression=Attr('email_verification_token_hash').eq(token_hash)
        )
        items = response.get('Items', [])
        logger.info(f"Scan found {len(items)} users with token hash")
        if not items:
            flash('Verification link is invalid or expired', 'error')
            return redirect(url_for('login'))

        user = items[0]
        users_table.update_item(
            Key={'email': user.get('email')},
            UpdateExpression="SET email_verified=:ev, updated_at=:ua REMOVE email_verification_token_hash",
            ExpressionAttributeValues={
                ':ev': True,
                ':ua': datetime.utcnow().isoformat()
            }
        )
        flash('Email verified. You can now log in.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        flash('An error occurred during verification', 'error')
        return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            response = users_table.get_item(Key={'email': email})
            user = response.get('Item')
            if user and user.get('email_verified', False):
                reset_token = secrets.token_urlsafe(32)
                reset_token_hash = _hash_token(reset_token)
                expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
                users_table.update_item(
                    Key={'email': email},
                    UpdateExpression="SET reset_token_hash=:th, reset_token_expires_at=:ea, updated_at=:ua",
                    ExpressionAttributeValues={
                        ':th': reset_token_hash,
                        ':ea': expires_at,
                        ':ua': datetime.utcnow().isoformat()
                    }
                )
                reset_link = url_for('reset_password', token=reset_token, _external=True)
                _send_email_via_sns(
                    'Reset your Stocker password',
                    f"Hi {user.get('name')},\n\nReset your password using the link below (valid for 30 minutes):\n{reset_link}\n\nIf you did not request this, you can ignore this email."
                )

            flash('If the email exists, a reset link has been sent.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            flash('An error occurred. Try again later.', 'error')

    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') if request.method == 'GET' else request.form.get('token')
    if not token:
        flash('Invalid reset link', 'error')
        return redirect(url_for('login'))

    token_hash = _hash_token(token)
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)
        if len(password or '') < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('reset_password.html', token=token)

        try:
            response = users_table.scan(
                FilterExpression=Attr('reset_token_hash').eq(token_hash)
            )
            items = response.get('Items', [])
            if not items:
                flash('Reset link is invalid or expired', 'error')
                return redirect(url_for('login'))

            user = items[0]
            expires_at = user.get('reset_token_expires_at')
            if not expires_at or datetime.utcnow() > datetime.fromisoformat(expires_at):
                flash('Reset link is invalid or expired', 'error')
                return redirect(url_for('login'))

            new_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
            users_table.update_item(
                Key={'email': user.get('email')},
                UpdateExpression="SET password_hash=:ph, updated_at=:ua REMOVE reset_token_hash, reset_token_expires_at, password",
                ExpressionAttributeValues={
                    ':ph': new_hash,
                    ':ua': datetime.utcnow().isoformat()
                }
            )
            flash('Password updated. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Reset password error: {str(e)}")
            flash('An error occurred. Try again later.', 'error')

    return render_template('reset_password.html', token=token)

# Dashboard Routes
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/buy-sell')
@login_required
def buy_sell():
    return render_template('buy_sell.html')

@app.route('/portfolio')
@login_required
def portfolio():
    return render_template('portfolio.html')

@app.route('/transactions')
@login_required
def transactions():
    return render_template('transactions.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# Admin Routes
@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
