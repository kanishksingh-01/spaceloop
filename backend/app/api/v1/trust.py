from flask import Blueprint, jsonify
trust_bp = Blueprint('trust', __name__)

@trust_bp.route('/ping', methods=['GET'])
def ping_trust():
    return jsonify({'module': 'trust', 'status': 'online'})
