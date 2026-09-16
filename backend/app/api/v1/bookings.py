from flask import Blueprint, jsonify
bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/ping', methods=['GET'])
def ping_bookings():
    return jsonify({'module': 'bookings', 'status': 'online'})
