"""
SpaceLoop Main Application & REST API
Zero-Hardware India Stack, Dual-Sided Document Verification, AI Micro-Leasing
Built for Hack2Ignite 2026 | Lead Dev: Kanishk Singh
"""

import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, abort
from models import db, User, Space, Booking, Review, SpaceInquiry, TelemetryLog
from security import (
    rate_limit_ai, sanitize_input, wrap_untrusted_notes,
    clamp_financial_bounds, add_security_headers,
    mask_aadhaar, hash_aadhaar, mask_student_id, mask_discom_ca, mask_upi_vpa
)
from telemetry import (
    verify_gps_geofence, generate_room_qr_token, generate_arrival_pin,
    calculate_punctuality_score, calculate_oti, execute_upi_escrow_refund
)
from india_stack import (
    verify_digilocker_aadhaar, verify_academic_credentials,
    verify_discom_meter, execute_upi_penny_drop, SUPPORTED_DISCOMS
)
from pricing import (
    calculate_dynamic_rate, calculate_host_monthly_yield, calculate_student_savings,
    CATEGORY_BASE_RATES
)
from space_ai import (
    inspect_space, match_spaces, synthesize_micro_lease,
    evaluate_condition_delta, concierge_chat, inquiry_pre_answer
)
from seed_data import seed_database


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'spaceloop_super_secret_hack2ignite_2026_key')
    
    # SQLite default database in workspace
    db_path = os.path.join(app.root_path, 'spaceloop.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # Injects security headers on every response
    @app.after_request
    def apply_defenses(response):
        return add_security_headers(response)

    # Persona session injector
    @app.context_processor
    def inject_persona():
        current_persona = session.get('persona', 'seeker')
        active_user_id = session.get('user_id', 1 if current_persona == 'seeker' else 3)
        user = User.query.get(active_user_id) if active_user_id else None
        return dict(current_persona=current_persona, current_user=user)

    # Initialize DB & Seed
    with app.app_context():
        db.create_all()
        seed_database()

    # ==========================================
    # FRONTEND WEB ROUTES
    # ==========================================
    @app.route('/')
    def index():
        category = request.args.get('category', '').strip()
        q = request.args.get('q', '').strip()

        query = Space.query.filter_by(is_active=True)
        if category and category.lower() != 'all':
            query = query.filter(Space.category.ilike(f"%{category}%"))
        if q:
            query = query.filter(
                (Space.title.ilike(f"%{q}%")) |
                (Space.address.ilike(f"%{q}%")) |
                (Space.city.ilike(f"%{q}%")) |
                (Space.description.ilike(f"%{q}%"))
            )
        spaces = query.all()

        total_spaces = Space.query.count()
        total_bookings = Booking.query.count()
        verified_students = User.query.filter_by(is_student_verified=True).count()

        return render_template(
            'index.html',
            spaces=spaces,
            selected_category=category or 'All',
            search_query=q,
            stats={
                'total_spaces': total_spaces,
                'total_bookings': total_bookings,
                'verified_students': verified_students,
                'avg_hourly_inr': 48
            }
        )

    @app.route('/space/<int:space_id>')
    def space_detail(space_id):
        space = Space.query.get_or_404(space_id)
        reviews = Review.query.filter_by(space_id=space.id).order_by(Review.created_at.desc()).all()
        inquiries = SpaceInquiry.query.filter_by(space_id=space.id).order_by(SpaceInquiry.created_at.desc()).limit(5).all()
        
        # Calculate OTI Proof-of-Reality score for this space
        oti_info = calculate_oti(
            punctuality=98.0,
            condition_match=space.ai_suitability_score,
            is_dual_verified=space.owner.is_host_verified if space.owner else True,
            dispute_count=0
        )

        return render_template('space_detail.html', space=space, reviews=reviews, inquiries=inquiries, oti=oti_info)

    @app.route('/space/<int:space_id>/printable-qr')
    def printable_qr(space_id):
        """Ready-to-print A4 Laminated Door Pass with cryptographic QR."""
        space = Space.query.get_or_404(space_id)
        return render_template('printable_qr.html', space=space)

    @app.route('/session/<int:booking_id>')
    def session_console(booking_id):
        """Live In-Room Session Console HUD."""
        booking = Booking.query.get_or_404(booking_id)
        space = booking.space
        return render_template('in_room.html', booking=booking, space=space)

    @app.route('/verify/student')
    def verify_student_page():
        return render_template('verify_student.html')

    @app.route('/verify/host')
    def verify_host_page():
        return render_template('verify_host.html', supported_discoms=SUPPORTED_DISCOMS)

    @app.route('/dashboard/seeker')
    def seeker_dashboard():
        user_id = session.get('user_id', 1)
        user = User.query.get(user_id) or User.query.first()
        bookings = Booking.query.filter_by(renter_id=user.id).order_by(Booking.created_at.desc()).all() if user else []
        return render_template('seeker_dashboard.html', user=user, bookings=bookings)

    @app.route('/dashboard/host')
    def host_dashboard():
        user_id = session.get('user_id', 3)
        user = User.query.get(user_id) or User.query.filter_by(role='owner').first()
        spaces = Space.query.filter_by(owner_id=user.id).all() if user else []
        space_ids = [s.id for s in spaces]
        bookings = Booking.query.filter(Booking.space_id.in_(space_ids)).order_by(Booking.created_at.desc()).all() if space_ids else []
        total_earnings = sum(b.total_price * 0.85 for b in bookings if b.session_state in ['checked_in', 'checked_out', 'completed'])
        return render_template('host_dashboard.html', user=user, spaces=spaces, bookings=bookings, total_earnings=round(total_earnings))

    @app.route('/calculator')
    def calculator_page():
        return render_template('calculator.html', categories=CATEGORY_BASE_RATES)

    @app.route('/lease/<int:booking_id>')
    def view_lease(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        return render_template('lease_view.html', booking=booking)

    # ==========================================
    # REST API CATALOGUE (as per Blueprint Section 8)
    # ==========================================
    @app.route('/api/spaces', methods=['GET'])
    def api_list_spaces():
        spaces = Space.query.filter_by(is_active=True).all()
        return jsonify([s.to_dict() for s in spaces])

    @app.route('/api/spaces/ai-scan', methods=['POST'])
    @rate_limit_ai(max_requests=20, window_seconds=60)
    def api_ai_scan():
        """Multimodal AI Space Inspector: Extracts sqft, lighting, noise dB,
        power circuits, suitability score, and fair price from photo and rough notes.
        """
        data = request.get_json() or {}
        category = sanitize_input(data.get('category', 'Workspace'), max_length=50)
        description = sanitize_input(data.get('description', ''), max_length=1500)
        photo_url = sanitize_input(data.get('photo_url', ''), max_length=300)
        address = sanitize_input(data.get('address', ''), max_length=200)

        result = inspect_space(category, description, photo_url, address)
        return jsonify(result)

    @app.route('/api/spaces/ai-match', methods=['POST'])
    @rate_limit_ai(max_requests=20, window_seconds=60)
    def api_ai_match():
        """Natural Language Matchmaker: Parses natural language intent query
        and ranks spaces with 0-100% compatibility score.
        """
        data = request.get_json() or {}
        query = sanitize_input(data.get('query', ''), max_length=300)
        if not query:
            return jsonify({'error': 'Query parameter required'}), 400

        all_spaces = [s.to_dict() for s in Space.query.filter_by(is_active=True).all()]
        match_result = match_spaces(query, all_spaces)
        return jsonify(match_result)

    @app.route('/api/bookings', methods=['POST'])
    def api_create_booking():
        """Creates booking: validates rate, recomputes financial figures server-side,
        requires Rs. 100 micro-escrow, and synthesizes Section 52 AI micro-lease agreement.
        """
        data = request.get_json() or {}
        space_id = data.get('space_id')
        hours = data.get('hours', 2.0)
        purpose = sanitize_input(data.get('purpose', 'Academic study and project development'), max_length=200)
        attendees = int(data.get('attendees_count', 1))

        space = Space.query.get(space_id)
        if not space:
            return jsonify({'error': 'Space not found'}), 404

        # Server-side financial recomputation & bounds clamping
        finance = clamp_financial_bounds(hours=hours, price_hourly=space.price_hourly)

        # Authenticate user from session or default seeker
        user_id = session.get('user_id')
        if not user_id:
            user = User.query.filter_by(role='seeker').first()
            user_id = user.id if user else 1
        renter = User.query.get(user_id)

        # Synthesize Section 52 Indian Easements Act Micro-Lease
        lease_meta = synthesize_micro_lease(
            space_title=space.title,
            space_address=space.address,
            host_name=space.owner.name if space.owner else "Verified Host",
            renter_name=renter.name if renter else "Verified Student",
            hours=finance['hours'],
            rate_hourly=space.price_hourly,
            purpose=purpose,
            attendees_count=attendees
        )

        now = datetime.utcnow()
        booking = Booking(
            space_id=space.id,
            renter_id=user_id,
            start_time=now,
            end_time=now + timedelta(hours=finance['hours']),
            hours_booked=finance['hours'],
            purpose=purpose,
            attendees_count=attendees,
            total_price=finance['rental_fee'],
            escrow_deposit_amount=finance['escrow_amount'],
            escrow_status='held',
            session_state='confirmed',
            arrival_pin=generate_arrival_pin(),
            micro_lease_agreement=lease_meta['agreement_text'],
            lease_hash=lease_meta['lease_hash']
        )
        db.session.add(booking)
        db.session.commit()

        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'space_title': space.title,
            'hours': finance['hours'],
            'hourly_rate': finance['hourly_rate'],
            'rental_fee': finance['rental_fee'],
            'escrow_deposit': finance['escrow_amount'],
            'total_payable': finance['total_payable'],
            'arrival_pin': booking.arrival_pin,
            'lease_hash': booking.lease_hash,
            'session_url': f"/session/{booking.id}"
        }), 201

    @app.route('/api/verify/student', methods=['POST'])
    def api_verify_student():
        """Student Verification Pipeline: DigiLocker Aadhaar OTP tokenization + .ac.in check.
        Complies strictly with Section 8 DPDP Act 2023.
        """
        data = request.get_json() or {}
        name = sanitize_input(data.get('name', 'Student'), max_length=100)
        aadhaar_num = data.get('aadhaar_number', '')
        otp = data.get('otp', '')
        college_email = sanitize_input(data.get('college_email', ''), max_length=120)
        college_name = sanitize_input(data.get('college_name', ''), max_length=150)
        student_id = sanitize_input(data.get('student_id', ''), max_length=50)

        # 1. Aadhaar verification via DigiLocker tokenization
        aadhaar_res = verify_digilocker_aadhaar(aadhaar_num, otp)
        if not aadhaar_res['success']:
            return jsonify(aadhaar_res), 400

        # 2. Institutional email verification
        acad_res = verify_academic_credentials(college_email, student_id, college_name)
        if not acad_res['success']:
            return jsonify(acad_res), 400

        # Update or create user record
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else User.query.filter_by(role='seeker').first()
        if user:
            user.name = name
            user.is_student_verified = True
            user.is_aadhaar_verified = True
            user.aadhaar_masked = aadhaar_res['masked_aadhaar']
            user.aadhaar_token_hash = aadhaar_res['token_hash']
            user.college_email = acad_res['college_email']
            user.college_name = acad_res['college_name']
            user.student_id_masked = acad_res['student_id_masked']
            user.objective_trust_score = min(100.0, user.objective_trust_score + 10.0)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Dual-layer Student Verification Completed (<20s). Subsidized rates unlocked.',
            'masked_aadhaar': aadhaar_res['masked_aadhaar'],
            'college_verified': acad_res['college_name'],
            'student_id_masked': acad_res['student_id_masked']
        })

    @app.route('/api/verify/host', methods=['POST'])
    def api_verify_host():
        """Host & Premise Verification Pipeline: State Discom CA bill validation
        and NPCI UPI Rs. 1 Penny Drop account verification.
        """
        data = request.get_json() or {}
        ca_number = data.get('ca_number', '')
        provider = sanitize_input(data.get('provider', 'BESCOM'), max_length=50)
        address = sanitize_input(data.get('address', ''), max_length=200)
        pan_name = sanitize_input(data.get('pan_name', 'Host Owner'), max_length=100)
        upi_vpa = sanitize_input(data.get('upi_vpa', ''), max_length=100)

        # 1. Discom verification
        discom_res = verify_discom_meter(ca_number, provider, address)
        if not discom_res['success']:
            return jsonify(discom_res), 400

        # 2. UPI Rs. 1 Penny Drop
        upi_res = execute_upi_penny_drop(upi_vpa, pan_name)
        if not upi_res['success']:
            return jsonify(upi_res), 400

        # Update host profile
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else User.query.filter_by(role='owner').first()
        if user:
            user.is_host_verified = True
            user.discom_provider = discom_res['provider']
            user.discom_ca_masked = discom_res['discom_ca_masked']
            user.upi_vpa_masked = upi_res['upi_vpa_masked']
            user.objective_trust_score = min(100.0, user.objective_trust_score + 12.0)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Host & Premise Verified (<15s). Meter confirmed active & UPI payout ready.',
            'discom': discom_res,
            'penny_drop': upi_res
        })

    @app.route('/api/booking/<int:booking_id>/check-in', methods=['POST'])
    def api_check_in(booking_id):
        """Zero-Hardware Physical Check-in Handshake.
        Validates room QR token and evaluates GPS Haversine distance <50m.
        """
        booking = Booking.query.get_or_404(booking_id)
        space = booking.space
        data = request.get_json() or {}

        qr_token = data.get('qr_token', '').strip()
        user_lat = float(data.get('lat', 0.0))
        user_lng = float(data.get('lng', 0.0))
        entry_photo = data.get('entry_photo', '')

        # 1. Validate Door Pass QR Token
        if qr_token != space.room_qr_token:
            return jsonify({
                'error': 'Invalid Room QR Token',
                'message': 'Scanned QR token does not match this space.'
            }), 400

        # 2. Haversine GPS Geofence Test (<50m radar)
        is_within, distance_meters = verify_gps_geofence(
            user_lat=user_lat, user_lng=user_lng,
            space_lat=space.latitude, space_lng=space.longitude,
            radius_meters=space.geofence_radius_meters
        )

        if not is_within:
            return jsonify({
                'error': 'Geofence Violation',
                'message': f'GPS Radar check failed! You are {distance_meters}m away. Must be within 50m of property.',
                'distance_meters': distance_meters,
                'max_allowed_meters': space.geofence_radius_meters
            }), 400

        # Record successful check-in
        booking.session_state = 'checked_in'
        booking.arrival_time = datetime.utcnow()
        booking.checkin_gps_lat = user_lat
        booking.checkin_gps_lng = user_lng
        booking.checkin_distance_meters = distance_meters
        if entry_photo:
            booking.entry_photo_url = entry_photo

        # Log audit telemetry
        log = TelemetryLog(
            booking_id=booking.id,
            event_type='GPS_CHECKIN_SUCCESS',
            details=f"Verified GPS radar at {distance_meters}m. Door QR validated."
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'session_state': 'checked_in',
            'arrival_pin': booking.arrival_pin,
            'physical_access_type': space.physical_access_type,
            'keybox_code': space.keybox_code,
            'distance_meters': distance_meters,
            'message': 'Check-in successful! Show dynamic arrival PIN to caretaker or enter code on mechanical keybox.'
        })

    @app.route('/api/booking/<int:booking_id>/check-out', methods=['POST'])
    def api_check_out(booking_id):
        """Zero-Hardware Physical Check-out & Instant UPI Escrow Release.
        Executes AI visual delta, verifies fans/lights off, calculates punctuality,
        and triggers instant Rs. 100 UPI refund.
        """
        booking = Booking.query.get_or_404(booking_id)
        space = booking.space
        data = request.get_json() or {}

        exit_photo = data.get('exit_photo', '')
        now = datetime.utcnow()

        # 1. Computer Vision Condition Delta & Appliance Check
        cv_eval = evaluate_condition_delta(
            entry_photo_url=booking.entry_photo_url,
            exit_photo_url=exit_photo,
            space_category=space.category
        )

        # 2. Punctuality Telemetry calculation
        punctuality = calculate_punctuality_score(
            start_time=booking.start_time,
            end_time=booking.end_time,
            actual_exit_time=now,
            grace_minutes=10
        )

        booking.session_state = 'checked_out'
        booking.departure_time = now
        booking.condition_match_score = cv_eval['condition_match_score']
        booking.appliances_shut_off = cv_eval['appliances_off']
        booking.punctuality_score = punctuality

        # 3. Instant Rs. 100 UPI Micro-Escrow Release Protocol
        renter_vpa = booking.renter.upi_vpa_masked if booking.renter and booking.renter.upi_vpa_masked else "student@upi"
        escrow_result = execute_upi_escrow_refund(
            renter_vpa=renter_vpa,
            condition_match_score=cv_eval['condition_match_score']
        )

        booking.escrow_status = escrow_result['status']
        booking.refund_tx_hash = escrow_result['transaction_ref']

        # Log audit telemetry
        log = TelemetryLog(
            booking_id=booking.id,
            event_type='CHECKOUT_DIFF_COMPLETE',
            details=f"Punctuality: {punctuality}%, CV Condition Match: {cv_eval['condition_match_score']}%, Escrow: {escrow_result['status']}"
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'session_state': 'checked_out',
            'punctuality_score': punctuality,
            'condition_match_score': cv_eval['condition_match_score'],
            'appliances_off': cv_eval['appliances_off'],
            'appliance_status': cv_eval['appliance_status'],
            'escrow_refund': escrow_result,
            'message': 'Check-out completed! Rs. 100 UPI escrow refund processed.' if escrow_result['success'] else 'Check-out recorded. Escrow held for review.'
        })

    @app.route('/api/concierge', methods=['POST'])
    @rate_limit_ai(max_requests=20, window_seconds=60)
    def api_concierge():
        """LoopBot AI Concierge multi-turn conversation endpoint."""
        data = request.get_json() or {}
        message = sanitize_input(data.get('message', ''), max_length=400)
        history = data.get('history', [])
        space_id = data.get('space_id')
        current_space = Space.query.get(space_id).to_dict() if space_id else None
        persona = session.get('persona', 'seeker')

        bot_reply = concierge_chat(message, history, current_space, persona)
        return jsonify({'reply': bot_reply})

    @app.route('/api/space/<int:space_id>/inquire', methods=['POST'])
    def api_space_inquiry(space_id):
        """In-App Inquiry Dispatch: AI pre-answers routine questions using verified metadata."""
        space = Space.query.get_or_404(space_id)
        data = request.get_json() or {}
        question = sanitize_input(data.get('question', ''), max_length=400)

        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400

        user_id = session.get('user_id', 1)
        ai_reply = inquiry_pre_answer(space.to_dict(), question)

        inquiry = SpaceInquiry(
            space_id=space.id,
            user_id=user_id,
            question=question,
            ai_answer=ai_reply,
            is_resolved=True
        )
        db.session.add(inquiry)
        db.session.commit()

        return jsonify({
            'success': True,
            'question': question,
            'ai_answer': ai_reply,
            'created_at': inquiry.created_at.strftime('%H:%M')
        })

    @app.route('/api/calculate-yield', methods=['POST'])
    def api_calculate_yield():
        """Dynamic Pricing & Yield Calculator endpoint."""
        data = request.get_json() or {}
        category = sanitize_input(data.get('category', 'Workspace'), max_length=50)
        sqft = float(data.get('sqft', 150))
        days = int(data.get('occupancy_days', 12))
        hours = float(data.get('hours_per_day', 6.0))

        rate_info = calculate_dynamic_rate(category, sqft)
        yield_info = calculate_host_monthly_yield(
            hourly_rate=rate_info['calculated_hourly'],
            occupancy_days_per_month=days,
            hours_per_day=hours
        )
        savings_info = calculate_student_savings(
            hours_needed=4.0,
            space_hourly_rate=rate_info['calculated_hourly']
        )

        return jsonify({
            'rate': rate_info,
            'yield': yield_info,
            'savings': savings_info
        })

    @app.route('/api/spaces/create', methods=['POST'])
    def api_create_space():
        """Host portal creates new micro-space listing."""
        data = request.get_json() or {}
        title = sanitize_input(data.get('title', 'New Micro-Space'), max_length=150)
        category = sanitize_input(data.get('category', 'Workspace'), max_length=50)
        description = sanitize_input(data.get('description', ''), max_length=1500)
        address = sanitize_input(data.get('address', 'Delhi'), max_length=200)
        city = sanitize_input(data.get('city', 'Delhi'), max_length=80)
        sqft = max(30, min(25000, int(data.get('sqft', 150))))
        price_hourly = max(10.0, float(data.get('price_hourly', 45.0)))
        image_url = sanitize_input(data.get('image_url', 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80'), max_length=300)

        # Default owner or session host
        user_id = session.get('user_id', 3)
        user = User.query.get(user_id)
        if not user or user.role != 'owner':
            user = User.query.filter_by(role='owner').first()
            user_id = user.id if user else 3

        # Generate unique room QR token
        temp_id = Space.query.count() + 1
        room_token = generate_room_qr_token(temp_id)

        new_space = Space(
            owner_id=user_id,
            title=title,
            category=category,
            description=description,
            address=address,
            city=city,
            latitude=float(data.get('latitude', 28.5450)),
            longitude=float(data.get('longitude', 77.1926)),
            geofence_radius_meters=50.0,
            room_qr_token=room_token,
            physical_access_type=data.get('physical_access_type', 'caretaker'),
            keybox_code=str(data.get('keybox_code', '4821')),
            sqft=sqft,
            max_capacity=int(data.get('max_capacity', 2)),
            price_hourly=price_hourly,
            price_daily=round(price_hourly * 7.5),
            ai_suitability_score=int(data.get('ai_suitability_score', 95)),
            ai_lighting=sanitize_input(data.get('ai_lighting', 'Natural Ambient + Task LED'), max_length=100),
            ai_noise_level=sanitize_input(data.get('ai_noise_level', 'Quiet (<34 dB)'), max_length=50),
            circuit_load=sanitize_input(data.get('circuit_load', '4x Grounded 20A Circuits'), max_length=100),
            amenities=sanitize_input(data.get('amenities', 'High-Speed Wi-Fi,Air Conditioning,Power Outlets'), max_length=300),
            image_url=image_url
        )
        db.session.add(new_space)
        db.session.commit()

        return jsonify({
            'success': True,
            'space_id': new_space.id,
            'room_qr_token': new_space.room_qr_token,
            'printable_qr_url': f"/space/{new_space.id}/printable-qr"
        }), 201

    @app.route('/api/persona/switch', methods=['POST'])
    def api_switch_persona():
        """Switches active demo persona between Seeker (student) and Host (space owner)."""
        data = request.get_json() or {}
        new_persona = data.get('persona', 'seeker').lower()
        if new_persona not in ['seeker', 'owner', 'host']:
            new_persona = 'seeker'
        
        target_role = 'owner' if new_persona in ['host', 'owner'] else 'seeker'
        user = User.query.filter_by(role=target_role).first()
        
        session['persona'] = target_role
        if user:
            session['user_id'] = user.id
        
        return jsonify({
            'success': True,
            'persona': target_role,
            'user_name': user.name if user else 'Active User',
            'redirect': '/dashboard/host' if target_role == 'owner' else '/'
        })

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found.'}), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate Limit Exceeded', 'message': 'AI sliding-window rate limit reached (20 calls/min).'}), 429

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n🚀 SpaceLoop platform running at: http://127.0.0.1:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
