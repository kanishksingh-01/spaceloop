import unittest
import json
from datetime import datetime, timedelta
from app import create_app
from models import db, Space, User, Booking
from backend.modules.search import (
    build_searchable_representation,
    generate_embedding,
    cosine_similarity,
    understand_search_query,
    hybrid_search_spaces,
)


class TestSemanticSearch(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_searchable_representation_contains_all_space_attributes(self):
        """Rich searchable representation includes title, description, category, location, amenities, capacity, uses."""
        space = Space(
            title="Kharadi Executive Boardroom",
            description="High-speed fiber and acoustic damping for remote teams.",
            category="Meeting",
            city="Pune",
            neighborhood="Kharadi",
            address="Kharadi IT Park",
            max_capacity=10,
            sqft=350,
            price_hourly=400.0,
            amenities=["Fiber WiFi", "Whiteboard", "4K TV", "Coffee Machine"],
            ai_recommended_uses="team meeting, client presentation, sprint planning",
            ai_noise_level="Acoustic treated quiet office",
            ai_tags=["corporate", "air-conditioned", "parking"]
        )
        text = build_searchable_representation(space)

        # Must not be only the title
        self.assertGreater(len(text), len(space.title))
        self.assertIn("Kharadi Executive Boardroom", text)
        self.assertIn("Meeting", text)
        self.assertIn("Kharadi", text)
        self.assertIn("Fiber WiFi", text)
        self.assertIn("10 people", text)
        self.assertIn("team meeting", text)
        self.assertIn("Acoustic treated quiet office", text)
        self.assertIn("corporate", text)

    def test_embedding_generation_and_cosine_similarity(self):
        """Embeddings are normalized float vectors; identical text yields cosine sim 1.0."""
        vec1 = generate_embedding("Quiet meeting room for 6 people with whiteboard")
        self.assertIsInstance(vec1, list)
        self.assertGreater(len(vec1), 0)
        self.assertIsInstance(vec1[0], float)

        # Same text should yield maximum cosine similarity
        sim_same = cosine_similarity(vec1, vec1)
        self.assertAlmostEqual(sim_same, 1.0, places=3)

        # Related text vs unrelated text
        vec_related = generate_embedding("Conference room with whiteboard for team meetings")
        vec_unrelated = generate_embedding("Open garage for auto repair and heavy welding")

        sim_rel = cosine_similarity(vec1, vec_related)
        sim_unrel = cosine_similarity(vec1, vec_unrelated)

        self.assertGreater(sim_rel, sim_unrel)

        # Cosine similarity handles empty or invalid inputs gracefully
        self.assertEqual(cosine_similarity([], vec1), 0.0)
        self.assertEqual(cosine_similarity(vec1, []), 0.0)
        self.assertEqual(cosine_similarity(None, vec1), 0.0)

    def test_query_understanding_factual_extraction_and_separation(self):
        """Natural query extracts location, capacity, hours, space type and keeps semantic query clean."""
        raw_query = "I need a quiet place for 6 people near Kharadi for a 4-hour team meeting"
        parsed = understand_search_query(raw_query)

        self.assertIn("semantic_query", parsed)

        # Capacity should be extracted
        self.assertEqual(parsed.get("capacity"), 6)

        # Hours should be extracted
        self.assertEqual(parsed.get("hours"), 4)

        # Location should contain Kharadi
        self.assertEqual(parsed.get("location"), "Kharadi")

        # Space type should be meeting
        self.assertEqual(parsed.get("space_type"), "Meeting")

        # Semantic query should remain meaningful
        self.assertTrue(len(parsed["semantic_query"]) > 0)

    def test_query_understanding_budget_and_amenity_extraction(self):
        """Extracts max budget and amenities without inventing missing values."""
        raw_query = "office space under ₹1000 per hour with fiber wifi and monitor"
        parsed = understand_search_query(raw_query)

        self.assertEqual(parsed.get("max_price"), 1000)
        has_wifi = any("wi-fi" in a.lower() or "wifi" in a.lower() for a in parsed.get("amenities", []))
        self.assertTrue(has_wifi)

    def test_deterministic_hard_filters_capacity_and_price(self):
        """Hard filters eliminate spaces with insufficient capacity or price above max."""
        with self.app.app_context():
            small_cheap = Space(
                title="Small Desk 1",
                description="Small single desk",
                address="Lane 1",
                category="Workspace",
                max_capacity=2,
                price_hourly=100.0,
                is_active=True
            )
            large_expensive = Space(
                title="Large Suite 2",
                description="Expensive large suite",
                address="Lane 2",
                category="Workspace",
                max_capacity=12,
                price_hourly=2000.0,
                is_active=True
            )
            perfect_fit = Space(
                title="Medium Room 3",
                description="Medium team space",
                address="Lane 3",
                category="Workspace",
                max_capacity=8,
                price_hourly=500.0,
                is_active=True
            )

            # Filter min capacity 6, max price 1000
            res = hybrid_search_spaces(
                raw_query="workspace",
                min_capacity=6,
                max_price=1000,
                candidate_spaces=[small_cheap, large_expensive, perfect_fit]
            )

            matched_ids = [r["space"]["title"] for r in res["results"]]
            self.assertIn("Medium Room 3", matched_ids)
            self.assertNotIn("Small Desk 1", matched_ids)  # Failed capacity
            self.assertNotIn("Large Suite 2", matched_ids)  # Failed price

    def test_deterministic_hard_filter_booking_availability(self):
        """Spaces with overlapping confirmed bookings are strictly excluded from results."""
        with self.app.app_context():
            # Create a host and a seeker
            host = User.query.filter_by(email="host_test_avail@example.com").first()
            if not host:
                host = User(name="Host Avail", email="host_test_avail@example.com", role="host")
                host.set_password("pass1234")
                db.session.add(host)
                db.session.commit()

            seeker = User.query.filter_by(email="seeker_test_avail@example.com").first()
            if not seeker:
                seeker = User(name="Seeker Avail", email="seeker_test_avail@example.com", role="seeker")
                seeker.set_password("pass1234")
                db.session.add(seeker)
                db.session.commit()

            # Create test space
            booked_space = Space.query.filter_by(title="Kharadi Locked Meeting Pod").first()
            if not booked_space:
                booked_space = Space(
                    title="Kharadi Locked Meeting Pod",
                    description="Private booked meeting pod in Kharadi.",
                    address="Kharadi Bypass Rd, Pune",
                    category="Meeting",
                    city="Pune",
                    neighborhood="Kharadi",
                    max_capacity=6,
                    price_hourly=300.0,
                    owner_id=host.id,
                    is_active=True
                )
                db.session.add(booked_space)
                db.session.commit()

            target_date = "2027-04-10"
            start_dt = datetime.fromisoformat(f"{target_date}T10:00:00")
            end_dt = datetime.fromisoformat(f"{target_date}T14:00:00")

            # Create confirmed overlapping booking
            existing_booking = Booking.query.filter_by(space_id=booked_space.id, start_time=start_dt).first()
            if not existing_booking:
                existing_booking = Booking(
                    space_id=booked_space.id,
                    renter_id=seeker.id,
                    start_time=start_dt,
                    end_time=end_dt,
                    total_price=1200.0,
                    status="confirmed",
                    intended_purpose="Team Meeting"
                )
                db.session.add(existing_booking)
                db.session.commit()

            # Search during that exact time window
            res = hybrid_search_spaces(
                raw_query="meeting room",
                date=target_date,
                start_time="10:00",
                end_time="14:00",
                candidate_spaces=[booked_space]
            )

            # Booked space must be excluded deterministically
            matched_titles = [r["space"]["title"] for r in res["results"]]
            self.assertNotIn("Kharadi Locked Meeting Pod", matched_titles)

    def test_space_creation_generates_embedding(self):
        """Listing a new space automatically populates its embedding_json."""
        with self.app.app_context():
            space = Space(
                title="Automated Embedding Test Space",
                description="Professional acoustic room for sound engineers.",
                address="Viman Nagar Main Rd",
                category="Studio",
                city="Pune",
                neighborhood="Viman Nagar",
                max_capacity=4,
                price_hourly=350.0,
                is_active=True
            )
            # Run update_embedding
            space.update_embedding(commit=False)

            self.assertIsNotNone(space.embedding_json)
            self.assertIsInstance(space.embedding, list)
            self.assertGreater(len(space.embedding), 10)

    def test_api_spaces_search_endpoint(self):
        """POST /api/spaces/search returns structured constraints and results."""
        res = self.client.post("/api/spaces/search", json={
            "query": "quiet place for 4 people near Hauz Khas for a team meeting",
            "capacity": 4
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("results", data)
        self.assertIn("spaces", data)
        self.assertIn("extracted_constraints", data)
        self.assertIn("total_matches", data)

        # Check result format
        if len(data["results"]) > 0:
            first = data["results"][0]
            self.assertIn("space", first)
            self.assertIn("match_reasons", first)
            self.assertIn("composite_score", first)
            self.assertIn("match_score", first)
            self.assertIn("availability_status", first)

    def test_api_spaces_ai_match_compatibility(self):
        """POST /api/spaces/ai-match remains 100% backward compatible for legacy clients."""
        res = self.client.post("/api/spaces/ai-match", json={
            "query": "Quiet place for 4 students to work on a hackathon near Hauz Khas"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("results", data)
        self.assertIn("spaces", data)
        self.assertGreater(len(data["results"]), 0)
        first = data["results"][0]
        self.assertIn("match_score", first)
        self.assertIn("space", first)

    def test_graceful_fallback_when_query_has_no_llm_or_embedding_error(self):
        """Fallback to deterministic keyword and attribute matching succeeds smoothly."""
        with self.app.app_context():
            space = Space(
                title="Acoustic Photography Bay",
                description="Equipped with strobe lights and reflectors.",
                address="FC Road",
                category="Studio",
                city="Pune",
                is_active=True
            )
            # Search with fallback mode
            res = hybrid_search_spaces(
                raw_query="photography studio with strobe lights",
                candidate_spaces=[space]
            )
            self.assertGreater(res["total_matches"], 0)
            self.assertEqual(res["results"][0]["space"]["title"], "Acoustic Photography Bay")


if __name__ == "__main__":
    unittest.main()
