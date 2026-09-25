"""
SpaceLoop Trust & Safety Engine
The central orchestrator for marketplace fraud, collusion, and abuse prevention.
"""
import hashlib
from datetime import datetime
from models import db, User, Space, Booking, Review, RiskAssessment, DeviceSession
from backend.modules.trust_safety.signals import get_signal, SIGNALS
from backend.modules.trust_safety.rules import (
    evaluate_booking_rules,
    evaluate_listing_rules,
    evaluate_review_rules,
    evaluate_checkout_rules
)
from backend.modules.trust_safety.graph import build_marketplace_graph
from space_ai import _call_groq, _call_gemini, is_simulate_ai_failure


def record_device_session(
    user_id: int,
    user_agent: str = "",
    ip_address: str = "",
    device_token: str | None = None
) -> DeviceSession:
    """
    Records or updates a privacy-preserving device session for a user.
    """
    raw_sig = f"{user_agent}|{device_token or ''}"
    fingerprint = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()
    ip_hash = hashlib.sha256((ip_address or "127.0.0.1").encode("utf-8")).hexdigest()

    session = DeviceSession.query.filter_by(
        user_id=user_id,
        device_fingerprint=fingerprint
    ).first()

    now = datetime.utcnow()
    if session:
        session.last_seen_at = now
        session.ip_address = ip_address[:45]
        session.ip_hash = ip_hash
        session.user_agent = user_agent[:250]
    else:
        session = DeviceSession(
            user_id=user_id,
            device_fingerprint=fingerprint,
            ip_address=ip_address[:45],
            ip_hash=ip_hash,
            user_agent=user_agent[:250],
            last_seen_at=now,
            created_at=now
        )
        db.session.add(session)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return session


def generate_explainable_narrative(entity_type: str, signals: list[dict], fallback_evidence: str) -> str:
    """
    Synthesizes triggered signals into a concise, factual forensic explanation for human operators.
    Uses multi-tier LLM routing (Groq -> Gemini -> deterministic template fallback).
    """
    if not signals:
        return f"Normal activity verified. No risk indicators detected for this {entity_type}."

    signal_descriptions = [f"- {s.get('code')}: {s.get('evidence')}" for s in signals]
    evidence_block = "\n".join(signal_descriptions)

    if not is_simulate_ai_failure():
        prompt = (
            f"You are a Trust & Safety forensic analyst for SpaceLoop, a peer-to-peer physical-space marketplace.\n"
            f"Summarize the following detected risk signals for a {entity_type} into a concise, factual 2-sentence explanation for a human moderator.\n"
            f"Do not use buzzwords or declare absolute fraud. Emphasize factual behavioral patterns.\n\n"
            f"Signals:\n{evidence_block}\n\n"
            f"Summary:"
        )

        # Tier 1: Groq
        groq_res = _call_groq([{"role": "user", "content": prompt}], temperature=0.2)
        if groq_res and len(groq_res.strip()) > 15:
            return groq_res.strip()

        # Tier 2: Gemini
        gemini_res = _call_gemini(prompt)
        if gemini_res and len(gemini_res.strip()) > 15:
            return gemini_res.strip()

    # Tier 3: Deterministic Rule Synthesis Fallback
    summary_parts = [s.get("evidence") for s in signals if s.get("evidence")]
    base = " • ".join(summary_parts) if summary_parts else fallback_evidence
    return f"[Forensic Rule Synthesis] {base}"


class TrustSafetyEngine:

    @staticmethod
    def compute_composite_risk(triggered_signals: list[dict]) -> tuple[float, float, str, str]:
        """
        Calculates composite risk score [0.0, 1.0], confidence [0.0, 1.0], risk level, and recommended action.
        """
        if not triggered_signals:
            return 0.05, 0.95, "normal", "allow"

        # Diminishing marginal risk accumulation
        # R = 1 - product(1 - w_i)
        combined_prob = 1.0
        for s in triggered_signals:
            w = float(s.get("weight", 0.5))
            combined_prob *= (1.0 - w)

        raw_score = 1.0 - combined_prob
        risk_score = min(1.0, max(0.0, raw_score))

        # Confidence is higher with more signals and specific evidence
        confidence = min(0.98, 0.65 + (0.10 * len(triggered_signals)))

        # Calibrated risk tiers
        if risk_score >= 0.75:
            risk_level = "high_risk"
            recommended_action = "restrict_action" if any(s.get("code") in ("SELF_BOOKING", "ACCOUNT_TAKEOVER_RISK", "UNVERIFIED_STAY_REVIEW") for s in triggered_signals) else "hold_transaction"
        elif risk_score >= 0.50:
            risk_level = "suspicious"
            recommended_action = "restrict_action" if any(s.get("code") == "UNVERIFIED_STAY_REVIEW" for s in triggered_signals) else "hold_transaction"
        elif risk_score >= 0.25:
            risk_level = "unusual"
            recommended_action = "request_verification"
        else:
            risk_level = "normal"
            recommended_action = "allow"

        return round(risk_score, 4), round(confidence, 4), risk_level, recommended_action

    @staticmethod
    def record_device_session(user_id: int, device_fingerprint: str = "", ip_address: str = "", user_agent: str = "") -> DeviceSession:
        """Records an obfuscated client hardware/IP session (DPDP Act compliant)."""
        import hashlib
        salt = "spaceloop-security-salt"
        try:
            from flask import current_app
            if current_app:
                salt = current_app.config.get("SECRET_KEY", salt)
        except Exception:
            pass
        ip_hash = hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()[:32] if ip_address else ""
        fp = device_fingerprint or hashlib.sha256(f"{salt}:{user_agent}:{ip_address}".encode("utf-8")).hexdigest()[:32]

        session = DeviceSession(
            user_id=user_id,
            device_fingerprint=fp,
            ip_address=ip_address,
            ip_hash=ip_hash,
            user_agent=user_agent
        )
        db.session.add(session)
        db.session.commit()
        return session

    @classmethod
    def evaluate_booking(
        cls,
        seeker: User,
        space: Space,
        hours: float = 2.0,
        total_price: float = 300.0,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        persist: bool = True
    ) -> RiskAssessment:
        """
        Evaluates risk on a proposed booking reservation.
        """
        graph = build_marketplace_graph()
        shared_infra = graph.find_shared_devices_and_ips(seeker.id, space.owner_id)

        signals = evaluate_booking_rules(
            seeker=seeker,
            space=space,
            hours=hours,
            total_price=total_price,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            shared_infrastructure_data=shared_infra
        )

        # Check for circular transaction loops in graph
        cycles = graph.detect_directed_cycles()
        if any(f"user:{seeker.id}" in c and f"user:{space.owner_id}" in c for c in cycles):
            signals.append({
                "code": "GRAPH_CIRCULAR_LOOP",
                "evidence": f"Seeker and Host participate in a circular multi-party booking ring.",
                "weight": 0.85
            })

        risk_score, confidence, risk_level, action = cls.compute_composite_risk(signals)
        evidence = generate_explainable_narrative("booking", signals, "Standard booking pattern.")

        assessment = RiskAssessment(
            entity_type="booking",
            entity_id=space.id,  # Associated space ID before booking row is inserted
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            signals_json=signals,
            evidence_text=evidence,
            recommended_action=action,
            action_taken="allowed" if action == "allow" else ("held" if action == "hold_transaction" else "flagged")
        )

        if persist:
            try:
                db.session.add(assessment)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return assessment

    @classmethod
    def evaluate_listing(
        cls,
        space: Space,
        owner: User,
        persist: bool = True
    ) -> RiskAssessment:
        """
        Evaluates risk on a newly created or edited space listing.
        """
        existing_spaces = Space.query.filter(Space.is_active == True).all()
        signals = evaluate_listing_rules(space, owner, existing_spaces)

        risk_score, confidence, risk_level, action = cls.compute_composite_risk(signals)
        evidence = generate_explainable_narrative("listing", signals, "Verified premise listing attributes.")

        assessment = RiskAssessment(
            entity_type="space",
            entity_id=space.id or 0,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            signals_json=signals,
            evidence_text=evidence,
            recommended_action=action,
            action_taken="allowed" if action == "allow" else "flagged"
        )

        if persist:
            try:
                db.session.add(assessment)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return assessment

    @classmethod
    def evaluate_review(
        cls,
        user: User | None = None,
        space: Space | None = None,
        booking: Booking | None = None,
        comment: str = "",
        rating: int = 5,
        reviewer: User | None = None,
        persist: bool = True
    ) -> RiskAssessment:
        """
        Evaluates risk on a submitted review.
        """
        target_user = user or reviewer
        signals = evaluate_review_rules(target_user, space, booking, comment)

        risk_score, confidence, risk_level, action = cls.compute_composite_risk(signals)
        evidence = generate_explainable_narrative("review", signals, "Verified stay review.")

        assessment = RiskAssessment(
            entity_type="review",
            entity_id=space.id if space else 0,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            signals_json=signals,
            evidence_text=evidence,
            recommended_action=action,
            action_taken="allowed" if action == "allow" else "blocked"
        )

        if persist:
            try:
                db.session.add(assessment)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return assessment

    @classmethod
    def evaluate_checkout(
        cls,
        booking: Booking,
        persist: bool = True
    ) -> RiskAssessment:
        """
        Evaluates risk on a completed booking session prior to escrow release.
        """
        signals = evaluate_checkout_rules(booking)

        risk_score, confidence, risk_level, action = cls.compute_composite_risk(signals)
        evidence = generate_explainable_narrative("checkout", signals, "Session completed within normal parameters.")

        assessment = RiskAssessment(
            entity_type="booking",
            entity_id=booking.id,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            signals_json=signals,
            evidence_text=evidence,
            recommended_action=action,
            action_taken="allowed" if action == "allow" else "held"
        )

        if persist:
            try:
                db.session.add(assessment)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return assessment

