from flask import Blueprint, jsonify
notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/ping', methods=['GET'])
def ping_notifications():
    return jsonify({'module': 'notifications', 'status': 'online'})
