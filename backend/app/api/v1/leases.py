from flask import Blueprint, jsonify
leases_bp = Blueprint('leases', __name__)

@leases_bp.route('/ping', methods=['GET'])
def ping_leases():
    return jsonify({'module': 'leases', 'status': 'online'})
