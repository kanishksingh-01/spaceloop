from flask import jsonify

def success_response(data, status_code=200):
    return jsonify({'success': True, 'data': data}), status_code

def error_response(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code
