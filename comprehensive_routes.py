"""
Comprehensive features routes following SOLID principles.

This module contains HTTP controllers for comprehensive features like goals and analytics.
Each route has a single responsibility: handling HTTP requests and responses.
Business logic is delegated to service layer components.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from typing import Dict, Any

comprehensive_bp = Blueprint('comprehensive', __name__)

class ComprehensiveController:
    """
    Controller for comprehensive features - Single Responsibility Principle.
    
    Handles HTTP concerns only, delegates business logic to services.
    """
    
    def __init__(self):
        """Initialize controller with minimal dependencies."""
        pass
    
    def render_dashboard(self, template_name: str, additional_context: Dict[str, Any] = None) -> str:
        """
        Render dashboard template with common context - DRY principle.
        
        Args:
            template_name: Name of the template to render
            additional_context: Additional context variables for the template
            
        Returns:
            Rendered HTML template
        """
        context = {
            'user': current_user
        }
        
        if additional_context:
            context.update(additional_context)
            
        return render_template(template_name, **context)

# Initialize controller instance
controller = ComprehensiveController()

@comprehensive_bp.route('/features/goals')
@login_required
def goals():
    """
    Goals dashboard route - Single Responsibility Principle.
    
    Handles HTTP request for goals dashboard, delegates rendering to controller.
    """
    return controller.render_dashboard('goals_dashboard.html')

@comprehensive_bp.route('/features/analytics')
@login_required
def analytics():
    """
    Analytics dashboard route - Single Responsibility Principle.
    
    Handles HTTP request for analytics dashboard, delegates rendering to controller.
    """
    return controller.render_dashboard('analytics_dashboard.html')
