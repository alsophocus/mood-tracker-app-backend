"""
SQL operations routes following SOLID principles
Database management interface with Material Design 3
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from database import db
from admin_services import AdminService

sql_bp = Blueprint('sql', __name__, url_prefix='/sql')

@sql_bp.route('/')
@login_required
def sql_dashboard():
    """SQL operations dashboard with Material Design 3"""
    admin_service = AdminService(db)
    operations = admin_service.get_available_operations()
    
    # Group operations by category
    grouped_ops = {}
    for op in operations:
        category = op['category']
        if category not in grouped_ops:
            grouped_ops[category] = []
        grouped_ops[category].append(op)
    
    return render_template('sql_dashboard.html', 
                         operations=grouped_ops,
                         user=current_user)

@sql_bp.route('/api/operations')
@login_required
def get_operations():
    """Get available SQL operations"""
    admin_service = AdminService(db)
    return jsonify({
        'success': True,
        'operations': admin_service.get_available_operations()
    })

@sql_bp.route('/api/execute/<operation_id>', methods=['POST'])
@login_required
def execute_operation(operation_id):
    """Execute SQL operation"""
    admin_service = AdminService(db)
    
    # Get parameters from request
    params = request.get_json() or {}
    
    # Execute operation
    result = admin_service.execute_operation(
        operation_id, 
        params, 
        user_id=current_user.id
    )
    
    # Add success flag if not present
    if 'success' not in result:
        result['success'] = 'error' not in result
    
    return jsonify(result)

@sql_bp.route('/api/stats')
@login_required
def get_database_stats():
    """Get database statistics"""
    admin_service = AdminService(db)
    result = admin_service.execute_operation('database_stats')
    
    return jsonify({
        'success': True,
        'stats': result
    })
