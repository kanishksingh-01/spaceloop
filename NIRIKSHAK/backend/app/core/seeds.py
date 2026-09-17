import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import Role, User
from app.models.device import Device
from app.models.resource import ResourceClassification, Resource
from app.models.baseline import BehaviorBaseline
from app.models.policy import RiskPolicy
from app.services.policy_service import DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS

logger = logging.getLogger(__name__)


async def seed_policies_if_missing(session) -> None:
    result = await session.execute(select(RiskPolicy).limit(1))
    if not result.scalar_one_or_none():
        logger.info("Seeding default risk policies and thresholds...")
        for k, v in DEFAULT_WEIGHTS.items():
            session.add(
                RiskPolicy(
                    id=str(uuid.uuid4()),
                    key=k,
                    category="WEIGHT",
                    value=v,
                    description=f"Default weight for {k}",
                    updated_by="SYSTEM",
                )
            )
        for k, v in DEFAULT_THRESHOLDS.items():
            session.add(
                RiskPolicy(
                    id=str(uuid.uuid4()),
                    key=k,
                    category="THRESHOLD",
                    value=v,
                    description=f"Default threshold for {k}",
                    updated_by="SYSTEM",
                )
            )
        await session.commit()
        logger.info("Default risk policies seeded.")


async def seed_initial_data() -> None:
    """Populates synthetic seed fixtures if database is empty."""
    async with AsyncSessionLocal() as session:
        await seed_policies_if_missing(session)

        # Check if users already exist
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded. Skipping initial fixture population.")
            return

        logger.info("Database is empty. Seeding initial synthetic data fixtures...")

        # 1. Seed Roles
        role_analyst = Role(id=str(uuid.uuid4()), name="ANALYST", description="Security Operations Center Analyst")
        role_admin = Role(id=str(uuid.uuid4()), name="ADMIN", description="System Administrator")
        role_user = Role(id=str(uuid.uuid4()), name="USER", description="Standard Synthetic Employee")
        session.add_all([role_analyst, role_admin, role_user])
        await session.flush()

        # 2. Seed Pre-Seeded Demo Login Accounts
        analyst_sarah = User(
            id=str(uuid.uuid4()),
            external_identifier="ANALYST-01",
            username="analyst_sarah",
            hashed_password=get_password_hash("analyst123"),
            role_id=role_analyst.id,
            department="SECURITY",
            status="ACTIVE",
        )
        admin_vikram = User(
            id=str(uuid.uuid4()),
            external_identifier="ADMIN-01",
            username="admin_vikram",
            hashed_password=get_password_hash("admin123"),
            role_id=role_admin.id,
            department="SECURITY",
            status="ACTIVE",
        )
        session.add_all([analyst_sarah, admin_vikram])

        # 3. Seed Synthetic Users
        departments = ["DEFENSE_RD", "ENGINEERING", "SECURITY", "FINANCE", "HUMAN_RESOURCES"]
        synthetic_users = []
        for i in range(1, 11):
            user = User(
                id=str(uuid.uuid4()),
                external_identifier=f"USER-{i:03d}",
                username=f"user_{i:03d}",
                hashed_password=get_password_hash("demo_password_hash"),
                role_id=role_user.id,
                department=departments[(i - 1) % len(departments)],
                status="ACTIVE",
            )
            synthetic_users.append(user)
            session.add(user)
        await session.flush()

        # 4. Seed Resource Classifications
        class_public = ResourceClassification(id=str(uuid.uuid4()), level="PUBLIC", base_sensitivity_score=10, description="Public synthetic documents")
        class_internal = ResourceClassification(id=str(uuid.uuid4()), level="INTERNAL", base_sensitivity_score=25, description="Standard internal communications")
        class_confidential = ResourceClassification(id=str(uuid.uuid4()), level="CONFIDENTIAL", base_sensitivity_score=50, description="Proprietary synthetic source code")
        class_restricted = ResourceClassification(id=str(uuid.uuid4()), level="RESTRICTED", base_sensitivity_score=75, description="Personnel security records")
        class_critical = ResourceClassification(id=str(uuid.uuid4()), level="CRITICAL", base_sensitivity_score=90, description="Core defense operational algorithms")
        session.add_all([class_public, class_internal, class_confidential, class_restricted, class_critical])
        await session.flush()

        # 5. Seed Synthetic Resources
        repo_a = Resource(id=str(uuid.uuid4()), name="Operational Repository A", category="OPERATIONAL_DEFENSE", classification_id=class_critical.id, owner_department="DEFENSE_RD")
        repo_b = Resource(id=str(uuid.uuid4()), name="Engineering Repository B", category="SOURCE_CODE", classification_id=class_confidential.id, owner_department="ENGINEERING")
        repo_c = Resource(id=str(uuid.uuid4()), name="Threat Assessment Repository C", category="THREAT_INTEL", classification_id=class_restricted.id, owner_department="SECURITY")
        repo_d = Resource(id=str(uuid.uuid4()), name="Personnel Security Repository D", category="PERSONNEL", classification_id=class_restricted.id, owner_department="HUMAN_RESOURCES")
        repo_e = Resource(id=str(uuid.uuid4()), name="Public Documentation E", category="DOCUMENTATION", classification_id=class_public.id, owner_department="ENGINEERING")
        all_repos = [repo_a, repo_b, repo_c, repo_d, repo_e]
        session.add_all(all_repos)
        await session.flush()

        # 6. Seed Synthetic Devices
        devices = []
        for i, user in enumerate(synthetic_users[:5]):
            dev = Device(
                id=str(uuid.uuid4()),
                device_identifier=f"DEV-{101 + i}",
                owner_user_id=user.id,
                device_type="LAPTOP",
                registered=True,
                trust_level="TRUSTED",
            )
            devices.append(dev)
            session.add(dev)

        # Add an unregistered/unknown suspicious device
        unregistered_device = Device(
            id=str(uuid.uuid4()),
            device_identifier="DEV-999",
            owner_user_id=None,
            device_type="UNKNOWN_WORKSTATION",
            registered=False,
            trust_level="LOW",
        )
        devices.append(unregistered_device)
        session.add(unregistered_device)
        await session.flush()

        # 7. Seed Behavior Baselines for synthetic users
        for i, user in enumerate(synthetic_users):
            user_device_id = devices[i].id if i < len(devices) - 1 else devices[0].id
            baseline = BehaviorBaseline(
                id=str(uuid.uuid4()),
                user_id=user.id,
                typical_hours={"start": 9, "end": 18},
                typical_devices=[user_device_id],
                typical_resources=[repo_b.id, repo_e.id] if user.department == "ENGINEERING" else [repo_a.id],
                avg_daily_volume=15728640,  # 15 MB
                std_daily_volume=5242880,   # 5 MB
            )
            session.add(baseline)

        await session.commit()
        logger.info("Successfully seeded synthetic data: roles, demo accounts, synthetic users, devices, resources, and baselines.")
