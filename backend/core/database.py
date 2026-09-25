"""
SpaceLoop Database Core Module
- Sets up SQLite WAL mode & 5000ms busy timeout listeners for robust write concurrency.
- Provides dialect-agnostic schema migration and initialization (SQLite and PostgreSQL).
"""
import uuid
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine


def configure_engine_pragmas(db):
    """
    Attaches connection event listeners to enforce Write-Ahead Logging (WAL),
    busy timeout, and relational foreign keys on SQLite engines.
    """
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        # Only execute PRAGMAs for sqlite connections
        cursor = dbapi_connection.cursor()
        try:
            # Check if this is an SQLite connection
            if hasattr(dbapi_connection, "execute") and "sqlite" in type(dbapi_connection).__module__.lower():
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=5000")
                cursor.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        finally:
            cursor.close()


def ensure_database_schema(app, db):
    """
    Dialect-agnostic database migration & schema sync:
    Inspects existing tables and adds any missing columns dynamically
    across both SQLite and PostgreSQL.
    """
    with app.app_context():
        db.create_all()

        try:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()

            if "users" in table_names:
                existing_cols = {col["name"]: col for col in inspector.get_columns("users")}
                
                columns_to_ensure = [
                    ("public_id", "VARCHAR(36)"),
                    ("first_name", "VARCHAR(60)"),
                    ("last_name", "VARCHAR(60)"),
                    ("is_active", "BOOLEAN"),
                    ("is_email_verified", "BOOLEAN"),
                    ("is_admin", "BOOLEAN"),
                    ("last_login_at", "DATETIME"),
                    ("is_student_verified", "BOOLEAN"),
                    ("college_name", "VARCHAR(150)"),
                    ("college_email", "VARCHAR(120)"),
                    ("student_id_masked", "VARCHAR(50)"),
                    ("is_aadhaar_verified", "BOOLEAN"),
                    ("aadhaar_masked", "VARCHAR(30)"),
                    ("aadhaar_token_hash", "VARCHAR(64)"),
                    ("is_host_verified", "BOOLEAN"),
                    ("discom_provider", "VARCHAR(80)"),
                    ("discom_ca_masked", "VARCHAR(40)"),
                    ("upi_verified", "BOOLEAN"),
                    ("upi_vpa_masked", "VARCHAR(80)"),
                    ("bank_beneficiary_name", "VARCHAR(120)"),
                    ("objective_trust_score", "FLOAT"),
                    ("on_time_vacate_rate", "FLOAT"),
                    ("cleanliness_match_rate", "FLOAT"),
                    ("total_completed_hours", "FLOAT"),
                    ("dispute_count", "INTEGER"),
                    ("mfa_enabled", "BOOLEAN DEFAULT 0"),
                    ("totp_secret", "VARCHAR(256)")
                ]

                with db.engine.connect() as conn:
                    for col_name, col_type in columns_to_ensure:
                        if col_name not in existing_cols:
                            try:
                                conn.execute(db.text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                                conn.commit()
                            except Exception:
                                pass

            if "email_verification_tokens" in table_names:
                evt_cols = {col["name"]: col for col in inspector.get_columns("email_verification_tokens")}
                if "pending_email" not in evt_cols:
                    with db.engine.connect() as conn:
                        try:
                            conn.execute(db.text("ALTER TABLE email_verification_tokens ADD COLUMN pending_email VARCHAR(120)"))
                            conn.commit()
                        except Exception:
                            pass

            # Ensure public_id is populated for all existing users
            from models import User
            users_without_pid = User.query.filter((User.public_id == None) | (User.public_id == "")).all()
            if users_without_pid:
                for u in users_without_pid:
                    u.public_id = str(uuid.uuid4())
                    if not u.first_name and u.name:
                        parts = u.name.strip().split(" ", 1)
                        u.first_name = parts[0]
                        u.last_name = parts[1] if len(parts) > 1 else ""
                db.session.commit()

            # Auto-seed initial spaces and users if database is newly initialized and empty
            from models import Space
            if Space.query.first() is None:
                try:
                    from seed_data import seed_database
                    seed_database()
                except Exception as seed_err:
                    print(f"[DB_SCHEMA_INIT] Auto-seed note: {seed_err}")

        except Exception as e:
            print(f"[DB_SCHEMA_INIT] Note: {e}")
