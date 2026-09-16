from flask import Blueprint, jsonify
discovery_bp = Blueprint('discovery', __name__)

@discovery_bp.route('/ping', methods=['GET'])
def ping_discovery():
    return jsonify({'module': 'discovery', 'status': 'online'})
