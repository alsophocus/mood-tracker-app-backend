"""
Web endpoint for testing migrations directly on deployed Railway app
"""

from flask import Blueprint, jsonify, request, current_app
from admin_services import AdminService
from database import db
import traceback

# Create blueprint for migration testing
migration_bp = Blueprint('migration_test', __name__, url_prefix='/migration-test')

@migration_bp.route('/basic', methods=['GET', 'POST'])
def test_basic_migration():
    """Test basic migration operation via web endpoint"""
    try:
        # Initialize AdminService with database instance
        admin_service = AdminService(db)
        # Use the correct method to execute basic migration
        result = admin_service.execute_operation('migrate_basic')
        
        response = {
            'success': result.get('success', False),
            'result': result,
            'endpoint': 'basic_migration',
            'method': request.method,
            'app_context': True,
            'operation_id': 'migrate_basic'
        }
        
        if result.get('success'):
            response['message'] = '✅ Migration successful'
            return jsonify(response), 200
        else:
            response['message'] = '❌ Migration failed'
            response['error'] = result.get('error', 'Unknown error')
            return jsonify(response), 500
            
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'endpoint': 'basic_migration',
            'method': request.method,
            'message': '❌ Migration exception',
            'app_context': True
        }
        return jsonify(error_response), 500

@migration_bp.route('/status', methods=['GET'])
def migration_status():
    """Get migration testing status"""
    return jsonify({
        'status': 'Migration testing endpoint active',
        'endpoints': {
            'basic': '/migration-test/basic',
            'status': '/migration-test/status'
        },
        'methods': ['GET', 'POST'],
        'database_connected': db is not None,
        'available_operations': ['migrate_basic', 'check_permissions']
    })
