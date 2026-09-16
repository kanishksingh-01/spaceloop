from flask import Blueprint, jsonify
users_bp = Blueprint('users', __name__)

@users_bp.route('/ping', methods=['GET'])
def ping_users():
    return jsonify({'module': 'users', 'status': 'online'})
