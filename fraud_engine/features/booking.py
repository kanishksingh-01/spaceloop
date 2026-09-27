"""
SpaceLoop Feature Extraction Layer - Booking & Payment Features
Extracts booking frequency, velocity, cancellation cycles, payment failure rates,
refund frequency, and amount deviation using Pandas and NumPy.
"""
from datetime import datetime, timedelta
from typing import Optional, List
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from models import Booking, Space, FraudEventRecord
from fraud_engine.schemas import FraudEventInput, FraudEventType
from fraud_engine.features.base import BaseFeatureExtractor, FeatureTrace, FeatureExtractionResult
from fraud_engine.features.similarity import calculate_modified_zscore


class BookingFeatureExtractor(BaseFeatureExtractor):
    """
    Extracts transaction velocity, cancellation churn, and financial deviation features.
    """

    @classmethod
    def extract(cls, event: FraudEventInput, db: Session, result: FeatureExtractionResult) -> None:
        now = datetime.utcnow()
        payload = event.payload or {}
        user_id = event.user_id

        # -------------------------------------------------------------
        # 1. Booking Amounts & Financial Deviation
        # -------------------------------------------------------------
        amount = float(payload.get("amount") or payload.get("total_price") or payload.get("price") or 0.0)
        hours = float(payload.get("hours_booked") or payload.get("hours") or 2.0)
        space_id = payload.get("space_id") or (event.entity_id if event.entity_type in ("space", "listing", "booking") else None)

        space = db.query(Space).filter(Space.id == space_id).first() if space_id else None

        amount_ratio_vs_space = 1.0
        if space and space.price_hourly and hours > 0:
            expected_price = space.price_hourly * hours
            if expected_price > 0 and amount > 0:
                amount_ratio_vs_space = float(round(amount / expected_price, 2))

        # Category-level price distribution modified Z-score
        category = space.category if space else str(payload.get("category") or "Storage")
        category_prices = [
            s[0] for s in db.query(Space.price_hourly).filter(
                Space.category == category,
                Space.is_active == True,
                Space.price_hourly > 0
            ).all()
        ]
        if not category_prices:
            category_prices = [s[0] for s in db.query(Space.price_hourly).filter(Space.is_active == True, Space.price_hourly > 0).all()]

        eff_rate = (amount / hours) if (amount > 0 and hours > 0) else (space.price_hourly if space else 0.0)
        mod_z = calculate_modified_zscore(eff_rate, category_prices)

        result.add(FeatureTrace(
            name="transaction_amount",
            value=float(round(amount, 2)),
            source="event.payload.amount / total_price",
            category="booking",
            description="Nominal transaction amount in INR (₹)."
        ))
        result.add(FeatureTrace(
            name="booking_amount",
            value=float(round(amount, 2)),
            source="event.payload.amount / total_price",
            category="booking",
            description="Total prospective or confirmed booking financial consideration."
        ))
        result.add(FeatureTrace(
            name="booking_amount_ratio_vs_space",
            value=amount_ratio_vs_space,
            source="amount / (space.price_hourly * hours)",
            category="booking",
            description="Ratio of transacted amount relative to space published hourly rate."
        ))
        result.add(FeatureTrace(
            name="price_zscore",
            value=mod_z,
            source="NumPy modified Z-score vs active category spaces",
            category="booking",
            description="Modified Z-score measuring statistical outlier deviation from category median."
        ))
        result.add(FeatureTrace(
            name="booking_amount_zscore_vs_category",
            value=mod_z,
            source="NumPy modified Z-score vs active category spaces",
            category="booking",
            description="Statistical price deviation relative to category peer listings."
        ))

        # -------------------------------------------------------------
        # 2. Bookings Frequency & Velocity
        # -------------------------------------------------------------
        b_count_15m = 0
        b_count_1h = 0
        b_count_24h = 0
        b_count_7d = 0
        seconds_since_last = 999999.0

        if user_id:
            window_15m = now - timedelta(minutes=15)
            window_1h = now - timedelta(hours=1)
            window_24h = now - timedelta(hours=24)
            window_7d = now - timedelta(days=7)

            # Query historical bookings for this user
            user_bookings = db.query(Booking.created_at, Booking.status).filter(
                Booking.renter_id == user_id,
                Booking.created_at >= window_7d
            ).order_by(Booking.created_at.desc()).all()

            if user_bookings:
                created_times = [b[0] for b in user_bookings if b[0]]
                b_count_7d = len(created_times)
                b_count_24h = sum(1 for t in created_times if t >= window_24h)
                b_count_1h = sum(1 for t in created_times if t >= window_1h)
                b_count_15m = sum(1 for t in created_times if t >= window_15m)

                if len(created_times) >= 1:
                    last_time = created_times[0]
                    seconds_since_last = max(0.0, float((now - last_time).total_seconds()))

        # If incoming event is booking_created, count it into window
        if event.event_type == FraudEventType.BOOKING_CREATED:
            b_count_15m += 1
            b_count_1h += 1
            b_count_24h += 1
            b_count_7d += 1

        velocity_rate_per_hour = float(round(b_count_24h / 24.0, 2))

        result.add(FeatureTrace(
            name="user_booking_count_15m",
            value=b_count_15m,
            source="db.bookings.renter_id[window=15m]",
            category="booking",
            description="Number of reservations initiated by the user in rolling 15 minutes."
        ))
        result.add(FeatureTrace(
            name="bookings_count_1h",
            value=b_count_1h,
            source="db.bookings.renter_id[window=1h]",
            category="booking",
            description="Total space bookings initiated by user in rolling 1 hour."
        ))
        result.add(FeatureTrace(
            name="bookings_count_24h",
            value=b_count_24h,
            source="db.bookings.renter_id[window=24h]",
            category="booking",
            description="Total space bookings initiated by user in rolling 24 hours."
        ))
        result.add(FeatureTrace(
            name="bookings_count_7d",
            value=b_count_7d,
            source="db.bookings.renter_id[window=7d]",
            category="booking",
            description="Total space bookings initiated by user in rolling 7 days."
        ))
        result.add(FeatureTrace(
            name="booking_velocity_rate_per_hour",
            value=velocity_rate_per_hour,
            source="bookings_count_24h / 24.0",
            category="booking",
            description="Average booking throughput rate per hour."
        ))
        result.add(FeatureTrace(
            name="seconds_since_last_booking",
            value=float(round(seconds_since_last, 1)),
            source="now - max(db.bookings.created_at)",
            category="booking",
            description="Elapsed time in seconds since the user's prior reservation creation."
        ))

        # -------------------------------------------------------------
        # 3. Cancellation Frequency & Ratios
        # -------------------------------------------------------------
        cancellations_24h = 0
        cancellations_7d = 0
        cancellations_30d = 0
        total_30d = 0
        ratio_7d = 0.0
        ratio_30d = 0.0

        if user_id:
            window_30d = now - timedelta(days=30)
            window_24h = now - timedelta(hours=24)
            window_7d = now - timedelta(days=7)

            records_30d = db.query(Booking.status, Booking.created_at).filter(
                Booking.renter_id == user_id,
                Booking.created_at >= window_30d
            ).all()

            if records_30d:
                df = pd.DataFrame(records_30d, columns=["status", "created_at"])
                df["created_at"] = pd.to_datetime(df["created_at"])
                total_30d = len(df)

                is_canc = df["status"] == "cancelled"
                cancellations_30d = int(is_canc.sum())
                cancellations_7d = int(((df["created_at"] >= pd.Timestamp(window_7d)) & is_canc).sum())
                cancellations_24h = int(((df["created_at"] >= pd.Timestamp(window_24h)) & is_canc).sum())

                total_7d = int((df["created_at"] >= pd.Timestamp(window_7d)).sum())
                ratio_7d = float(cancellations_7d / total_7d) if total_7d >= 2 else 0.0
                ratio_30d = float(cancellations_30d / total_30d) if total_30d >= 2 else 0.0

        if event.event_type == FraudEventType.BOOKING_CANCELLED:
            cancellations_24h += 1
            cancellations_7d += 1
            cancellations_30d += 1

        booking_to_cancel_ratio = float(round(total_30d / max(1, cancellations_30d), 2))

        result.add(FeatureTrace(
            name="cancellations_count_24h",
            value=cancellations_24h,
            source="db.bookings[renter_id, status=cancelled, window=24h]",
            category="booking",
            description="Number of reservation cancellations executed by user in last 24 hours."
        ))
        result.add(FeatureTrace(
            name="cancellations_count_7d",
            value=cancellations_7d,
            source="db.bookings[renter_id, status=cancelled, window=7d]",
            category="booking",
            description="Number of reservation cancellations executed by user in last 7 days."
        ))
        result.add(FeatureTrace(
            name="cancellations_count_30d",
            value=cancellations_30d,
            source="db.bookings[renter_id, status=cancelled, window=30d]",
            category="booking",
            description="Number of reservation cancellations executed by user in last 30 days."
        ))
        result.add(FeatureTrace(
            name="user_cancellation_ratio_7d",
            value=float(round(ratio_7d, 2)),
            source="cancellations_7d / total_7d",
            category="booking",
            description="Proportion of bookings cancelled by user over rolling 7 days."
        ))
        result.add(FeatureTrace(
            name="cancellation_ratio_7d",
            value=float(round(ratio_7d, 2)),
            source="cancellations_7d / total_7d",
            category="booking",
            description="Proportion of bookings cancelled by user over rolling 7 days."
        ))
        result.add(FeatureTrace(
            name="cancellation_ratio_30d",
            value=float(round(ratio_30d, 2)),
            source="cancellations_30d / total_30d",
            category="booking",
            description="Proportion of bookings cancelled by user over rolling 30 days."
        ))
        result.add(FeatureTrace(
            name="booking_to_cancellation_ratio",
            value=booking_to_cancel_ratio,
            source="total_bookings_30d / max(1, cancellations_30d)",
            category="booking",
            description="Ratio of total created reservations to cancellations over 30 days."
        ))
        result.add(FeatureTrace(
            name="user_total_bookings_7d",
            value=b_count_7d,
            source="db.bookings.renter_id[window=7d]",
            category="booking",
            description="Total bookings recorded for user across last 7 days."
        ))

        # -------------------------------------------------------------
        # 4. Payment Failures & Gateway Failure Rate
        # -------------------------------------------------------------
        pay_fails_15m = 0
        pay_fails_24h = 0
        pay_attempts_24h = 0
        fail_rate_24h = 0.0

        if user_id:
            window_15m = now - timedelta(minutes=15)
            window_24h = now - timedelta(hours=24)

            pay_events = db.query(FraudEventRecord.event_type, FraudEventRecord.created_at).filter(
                FraudEventRecord.user_id == user_id,
                FraudEventRecord.event_type.in_([
                    FraudEventType.PAYMENT_FAILED.value,
                    FraudEventType.PAYMENT_COMPLETED.value
                ]),
                FraudEventRecord.created_at >= window_24h
            ).all()

            if pay_events:
                df_pay = pd.DataFrame(pay_events, columns=["event_type", "created_at"])
                df_pay["created_at"] = pd.to_datetime(df_pay["created_at"])
                pay_attempts_24h = len(df_pay)
                is_failed = df_pay["event_type"] == FraudEventType.PAYMENT_FAILED.value

                pay_fails_24h = int(is_failed.sum())
                pay_fails_15m = int(((df_pay["created_at"] >= pd.Timestamp(window_15m)) & is_failed).sum())
                fail_rate_24h = float(pay_fails_24h / pay_attempts_24h) if pay_attempts_24h > 0 else 0.0

        if event.event_type == FraudEventType.PAYMENT_FAILED:
            pay_fails_15m += 1
            pay_fails_24h += 1
            pay_attempts_24h += 1
            fail_rate_24h = float(pay_fails_24h / pay_attempts_24h)

        result.add(FeatureTrace(
            name="failed_payment_count_15m",
            value=pay_fails_15m,
            source="db.fraud_events[type=payment_failed, window=15m]",
            category="booking",
            description="Count of failed payment transactions in rolling 15 minutes."
        ))
        result.add(FeatureTrace(
            name="payment_failures_24h",
            value=pay_fails_24h,
            source="db.fraud_events[type=payment_failed, window=24h]",
            category="booking",
            description="Total failed payment attempts in rolling 24 hours."
        ))
        result.add(FeatureTrace(
            name="payment_attempts_24h",
            value=pay_attempts_24h,
            source="db.fraud_events[payment_failed + payment_completed, window=24h]",
            category="booking",
            description="Total payment attempts recorded for user in 24 hours."
        ))
        result.add(FeatureTrace(
            name="payment_failure_rate_24h",
            value=float(round(fail_rate_24h, 2)),
            source="payment_failures_24h / max(1, payment_attempts_24h)",
            category="booking",
            description="Ratio of failed payment attempts to total attempts over 24 hours."
        ))

        # -------------------------------------------------------------
        # 5. Refund Frequency & Reversal Patterns
        # -------------------------------------------------------------
        refund_req_30d = 0
        refund_comp_30d = 0
        refund_amt_30d = 0.0

        if user_id:
            window_30d = now - timedelta(days=30)
            refund_events = db.query(
                FraudEventRecord.event_type,
                FraudEventRecord.payload_json
            ).filter(
                FraudEventRecord.user_id == user_id,
                FraudEventRecord.event_type.in_([
                    FraudEventType.REFUND_REQUESTED.value,
                    FraudEventType.REFUND_COMPLETED.value
                ]),
                FraudEventRecord.created_at >= window_30d
            ).all()

            for evt_type, evt_payload in refund_events:
                if evt_type == FraudEventType.REFUND_REQUESTED.value:
                    refund_req_30d += 1
                elif evt_type == FraudEventType.REFUND_COMPLETED.value:
                    refund_comp_30d += 1
                if isinstance(evt_payload, dict):
                    refund_amt_30d += float(evt_payload.get("amount") or 0.0)

        if event.event_type == FraudEventType.REFUND_REQUESTED:
            refund_req_30d += 1
            refund_amt_30d += float(payload.get("amount") or 0.0)
        elif event.event_type == FraudEventType.REFUND_COMPLETED:
            refund_comp_30d += 1
            refund_amt_30d += float(payload.get("amount") or 0.0)

        result.add(FeatureTrace(
            name="refund_requested_count_30d",
            value=refund_req_30d,
            source="db.fraud_events[type=refund_requested, window=30d]",
            category="booking",
            description="Total refund requests lodged by user in last 30 days."
        ))
        result.add(FeatureTrace(
            name="refund_completed_count_30d",
            value=refund_comp_30d,
            source="db.fraud_events[type=refund_completed, window=30d]",
            category="booking",
            description="Total refunds successfully disbursed to user in last 30 days."
        ))
        result.add(FeatureTrace(
            name="refund_amount_total_30d",
            value=float(round(refund_amt_30d, 2)),
            source="sum(db.fraud_events.payload.amount[refund, window=30d])",
            category="booking",
            description="Cumulative monetary value of refunds processed for user in 30 days."
        ))
