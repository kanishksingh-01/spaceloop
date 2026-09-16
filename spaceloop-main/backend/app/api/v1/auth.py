from flask import Blueprint, jsonify
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/ping', methods=['GET'])
def ping_auth():
    return jsonify({'module': 'auth', 'status': 'online'})
