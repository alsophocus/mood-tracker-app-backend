import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    
    # App Configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['DATABASE_URL']
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
        
        # Warn about missing OAuth but don't fail
        oauth_missing = []
        if not cls.GOOGLE_CLIENT_ID:
            oauth_missing.append('GOOGLE_CLIENT_ID')
        if not cls.GOOGLE_CLIENT_SECRET:
            oauth_missing.append('GOOGLE_CLIENT_SECRET')
        
        if oauth_missing:
            print(f"⚠️ Warning: OAuth not configured: {', '.join(oauth_missing)}")
            print("   Authentication will not work without OAuth credentials")
