from flask import jsonify

def handle_error(status_code, error_type, message):
    return jsonify({
        'error': error_type,
        'message': message
    }), status_code
