"""
Insights routes following SOLID principles.

This module contains HTTP controllers for insights dashboard.
Follows Single Responsibility Principle by separating HTTP concerns from business logic.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from typing import Dict, Any

insights_bp = Blueprint('insights', __name__)

class InsightsController:
    """
    Controller for insights features - Single Responsibility Principle.
    
    Handles HTTP concerns only, delegates business logic to services.
    """
    
    def __init__(self):
        """Initialize controller with minimal dependencies."""
        pass
    
    def render_insights_dashboard(self, additional_context: Dict[str, Any] = None) -> str:
        """
        Render insights dashboard with proper context.
        
        Args:
            additional_context: Additional context variables for the template
            
        Returns:
            Rendered HTML template
        """
        context = {
            'user': current_user
        }
        
        if additional_context:
            context.update(additional_context)
            
        return render_template('insights_dashboard.html', **context)

# Initialize controller instance
controller = InsightsController()

@insights_bp.route('/insights')
@login_required
def dashboard():
    """
    Insights dashboard route - Single Responsibility Principle.
    
    Handles HTTP request for insights dashboard, delegates rendering to controller.
    """
    return controller.render_insights_dashboard()
