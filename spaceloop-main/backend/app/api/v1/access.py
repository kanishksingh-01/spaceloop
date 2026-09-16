from flask import Blueprint, jsonify
access_bp = Blueprint('access', __name__)

@access_bp.route('/ping', methods=['GET'])
def ping_access():
    return jsonify({'module': 'access', 'status': 'online'})
