from flask import Blueprint, jsonify
verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/ping', methods=['GET'])
def ping_verification():
    return jsonify({'module': 'verification', 'status': 'online'})
