"""
Dependency injection container following SOLID principles
"""
from typing import Dict, Any
from config import Config
from database_new import create_repositories
from services import create_services, MoodServiceInterface, UserService, TimezoneServiceInterface

class DIContainer:
    """Dependency injection container - Single Responsibility Principle"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all dependencies - Open/Closed Principle for extension"""
        if self._initialized:
            return
        
        # Create repositories
        mood_repo, user_repo, db_connection = create_repositories(Config.DATABASE_URL)
        
        # Create services
        mood_service, user_service, timezone_service = create_services(
            mood_repo, mood_repo, user_repo, user_repo
        )
        
        # Register services
        self._services['mood_service'] = mood_service
        self._services['user_service'] = user_service
        self._services['timezone_service'] = timezone_service
        self._services['db_connection'] = db_connection
        
        # Register repositories for direct access if needed
        self._services['mood_repo'] = mood_repo
        self._services['user_repo'] = user_repo
        
        self._initialized = True
    
    def get_mood_service(self) -> MoodServiceInterface:
        """Get mood service"""
        self._ensure_initialized()
        return self._services['mood_service']
    
    def get_user_service(self) -> UserService:
        """Get user service"""
        self._ensure_initialized()
        return self._services['user_service']
    
    def get_timezone_service(self) -> TimezoneServiceInterface:
        """Get timezone service"""
        self._ensure_initialized()
        return self._services['timezone_service']
    
    def get_db_connection(self):
        """Get database connection"""
        self._ensure_initialized()
        return self._services['db_connection']
    
    def _ensure_initialized(self):
        """Ensure container is initialized"""
        if not self._initialized:
            self.initialize()

# Global container instance
container = DIContainer()
