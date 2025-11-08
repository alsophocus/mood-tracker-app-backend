from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import requests
import urllib.parse
from database import db
from config import Config

auth_bp = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, email, name, provider):
        self.id = id
        self.email = email
        self.name = name
        self.provider = provider

def init_auth(app):
    """Initialize authentication"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None  # Remove default message
    
    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for('auth.login'))
    
    @login_manager.user_loader
    def load_user(user_id):
        user_data = db.get_user(user_id)
        if user_data:
            return User(user_data['id'], user_data['email'], user_data['name'], user_data['provider'])
        return None

@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/auth/<provider>')
def oauth_login(provider):
    if provider not in ['google', 'github']:
        flash('Invalid OAuth provider')
        return redirect(url_for('auth.login'))
    
    client_id = getattr(Config, f'{provider.upper()}_CLIENT_ID')
    if not client_id:
        flash(f'{provider.title()} OAuth not configured')
        return redirect(url_for('auth.login'))
    
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True, _scheme='https')
    
    if provider == 'google':
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline'
        }
        auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
    else:  # github
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'user:email',
            'response_type': 'code'
        }
        auth_url = 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)
    
    return redirect(auth_url)

@auth_bp.route('/callback/<provider>')
def oauth_callback(provider):
    code = request.args.get('code')
    if not code:
        flash('No authorization code received')
        return redirect(url_for('auth.login'))
    
    try:
        user_info = _exchange_code_for_user_info(provider, code)
        if not user_info or not user_info.get('email'):
            flash('Could not get user information')
            return redirect(url_for('auth.login'))
        
        # Create or get user
        user_data = db.create_user(user_info['email'], user_info['name'], provider)
        user = User(user_data['id'], user_data['email'], user_data['name'], user_data['provider'])
        
        login_user(user)
        return redirect(url_for('main.index'))
        
    except Exception as e:
        flash(f'Authentication failed: {str(e)}')
        return redirect(url_for('auth.login'))

def _exchange_code_for_user_info(provider, code):
    """Exchange OAuth code for user information"""
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True, _scheme='https')
    
    if provider == 'google':
        # Exchange code for token
        token_data = {
            'client_id': Config.GOOGLE_CLIENT_ID,
            'client_secret': Config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_response.raise_for_status()
        
        access_token = token_response.json().get('access_token')
        if not access_token:
            raise ValueError('No access token received')
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
        user_response.raise_for_status()
        
        user_info = user_response.json()
        return {'email': user_info.get('email'), 'name': user_info.get('name')}
    
    elif provider == 'github':
        # Exchange code for token
        token_data = {
            'client_id': Config.GITHUB_CLIENT_ID,
            'client_secret': Config.GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {'Accept': 'application/json'}
        token_response = requests.post('https://github.com/login/oauth/access_token', 
                                     data=token_data, headers=headers)
        token_response.raise_for_status()
        
        access_token = token_response.json().get('access_token')
        if not access_token:
            raise ValueError('No access token received')
        
        # Get user info
        headers = {'Authorization': f'token {access_token}'}
        user_response = requests.get('https://api.github.com/user', headers=headers)
        user_response.raise_for_status()
        
        user_info = user_response.json()
        email = user_info.get('email')
        
        # Get email if private
        if not email:
            emails_response = requests.get('https://api.github.com/user/emails', headers=headers)
            if emails_response.status_code == 200:
                emails = emails_response.json()
                email = next((e['email'] for e in emails if e['primary']), None)
        
        return {'email': email, 'name': user_info.get('name') or user_info.get('login')}

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')
