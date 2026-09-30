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

            if "spaces" in table_names:
                space_cols = {col["name"]: col for col in inspector.get_columns("spaces")}
                if "embedding_json" not in space_cols:
                    with db.engine.connect() as conn:
                        try:
                            col_type = "JSON" if "postgres" in str(db.engine.url).lower() else "TEXT"
                            conn.execute(db.text(f"ALTER TABLE spaces ADD COLUMN embedding_json {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            if "reviews" in table_names:
                rev_cols = {col["name"]: col for col in inspector.get_columns("reviews")}
                if "booking_id" not in rev_cols:
                    with db.engine.connect() as conn:
                        try:
                            conn.execute(db.text("ALTER TABLE reviews ADD COLUMN booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE"))
                            conn.commit()
                        except Exception:
                            pass

            if "space_inquiries" in table_names:
                inq_cols = {col["name"]: col for col in inspector.get_columns("space_inquiries")}
                if "response" not in inq_cols:
                    with db.engine.connect() as conn:
                        try:
                            conn.execute(db.text("ALTER TABLE space_inquiries ADD COLUMN response TEXT DEFAULT ''"))
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

            # Ensure master demo & admin accounts always exist with verified status and known password
            try:
                from werkzeug.security import generate_password_hash
                demo_user = User.query.filter_by(email="demo@spaceloop.in").first()
                if not demo_user:
                    demo_user = User(
                        name="SpaceLoop Demo User",
                        first_name="SpaceLoop",
                        last_name="Demo",
                        email="demo@spaceloop.in",
                        password_hash=generate_password_hash("password123"),
                        role="both",
                        bio="Official SpaceLoop universal master demo account for testing seeker and host flows.",
                        phone="+91 98000 11223",
                        is_admin=True,
                        is_active=True,
                        is_email_verified=True,
                        is_host_verified=True,
                        discom_provider="TPDDL (Tata Power Delhi)",
                        discom_ca_masked="***1234",
                        upi_verified=True,
                        upi_vpa_masked="demo***@okhdfcbank",
                        bank_beneficiary_name="SpaceLoop Demo User",
                        is_student_verified=True,
                        college_name="IIT Delhi",
                        college_email="demo@iitd.ac.in",
                        student_id_masked="***9999",
                        is_aadhaar_verified=True,
                        aadhaar_masked="XXXXXXXX9999",
                        objective_trust_score=99.5,
                        on_time_vacate_rate=100.0,
                        cleanliness_match_rate=99.0,
                        total_completed_hours=50.0,
                        dispute_count=0,
                        mfa_enabled=False
                    )
                    db.session.add(demo_user)
                    db.session.commit()
                else:
                    demo_user.password_hash = generate_password_hash("password123")
                    demo_user.role = "both"
                    demo_user.is_admin = True
                    demo_user.is_active = True
                    demo_user.is_email_verified = True
                    demo_user.is_host_verified = True
                    demo_user.mfa_enabled = False
                    db.session.commit()

                admin_user = User.query.filter_by(email="admin@spaceloop.in").first()
                if not admin_user:
                    admin_user = User(
                        name="SpaceLoop Platform Admin",
                        first_name="Platform",
                        last_name="Admin",
                        email="admin@spaceloop.in",
                        password_hash=generate_password_hash("password123"),
                        role="both",
                        bio="SpaceLoop System Administrator & Safety Guardian.",
                        phone="+91 99999 00000",
                        is_admin=True,
                        is_active=True,
                        is_email_verified=True,
                        is_host_verified=True,
                        discom_provider="TPDDL (Tata Power Delhi)",
                        discom_ca_masked="***9999",
                        upi_verified=True,
                        upi_vpa_masked="admin***@oksbi",
                        bank_beneficiary_name="SpaceLoop Platform Admin",
                        objective_trust_score=100.0,
                        on_time_vacate_rate=100.0,
                        cleanliness_match_rate=100.0,
                        total_completed_hours=100.0,
                        dispute_count=0,
                        mfa_enabled=False
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                else:
                    admin_user.password_hash = generate_password_hash("password123")
                    admin_user.role = "both"
                    admin_user.is_admin = True
                    admin_user.is_active = True
                    admin_user.is_email_verified = True
                    admin_user.is_host_verified = True
                    admin_user.mfa_enabled = False
                    db.session.commit()
            except Exception as master_acc_err:
                db.session.rollback()
                print(f"[DB_SCHEMA_INIT] Master account provisioning note: {master_acc_err}")

            # Auto-seed initial spaces and users if database is newly initialized and empty
            from models import Space
            if Space.query.first() is None:
                try:
                    from seed_data import seed_database
                    seed_database()
                except Exception as seed_err:
                    print(f"[DB_SCHEMA_INIT] Auto-seed note: {seed_err}")

            # Ensure active spaces have embeddings indexed
            try:
                unembedded = Space.query.filter((Space.embedding_json == None) | (Space.embedding_json == "")).all()
                if unembedded:
                    from backend.modules.search.embedding import build_searchable_representation, generate_embedding
                    for sp in unembedded:
                        try:
                            txt = build_searchable_representation(sp)
                            sp.embedding = generate_embedding(txt)
                        except Exception:
                            pass
                    db.session.commit()
            except Exception as emb_err:
                db.session.rollback()
                print(f"[DB_SCHEMA_INIT] Embedding index note: {emb_err}")

        except Exception as e:
            print(f"[DB_SCHEMA_INIT] Note: {e}")
