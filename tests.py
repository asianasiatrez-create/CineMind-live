import os
import unittest

# Use a separate test database so production cinemind.db is untouched
os.environ["CINEMIND_DB"] = "test_cinemind.db"

import app as cinemind_app


class CineMindIntegrationTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cinemind_app.DB_NAME = "test_cinemind.db"
        if os.path.exists("test_cinemind.db"):
            os.remove("test_cinemind.db")
        cinemind_app.init_db()
        cls.client = cinemind_app.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("test_cinemind.db"):
            try:
                os.remove("test_cinemind.db")
            except Exception:
                pass

    def test_01_health_check_and_tables(self):
        """Test API root health check and verify 6 related tables are registered."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("audit_logs", data["database_tables"])
        self.assertEqual(len(data["database_tables"]), 6)

    def test_02_signup_validation_and_user_creation(self):
        """Test input validation on signup and standard user role assignment."""
        # Short password should fail with 400
        bad_res = self.client.post("/api/signup", json={"username": "tester1", "password": "123"})
        self.assertEqual(bad_res.status_code, 400)

        # Valid signup should succeed and assign 'user' role
        ok_res = self.client.post("/api/signup", json={
            "username": "tester1",
            "password": "securepassword123",
            "genres": ["28", "878", "BL"]
        })
        self.assertEqual(ok_res.status_code, 200)
        data = ok_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "user")

    def test_03_admin_role_creation_and_login(self):
        """Test Role-Based Access Control (RBAC) for admin accounts."""
        res = self.client.post("/api/signup", json={
            "username": "admin_panel",
            "password": "adminpassword123",
            "genres": ["99", "SPORTS", "18"]
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["role"], "admin")

        login_res = self.client.post("/api/login", json={
            "username": "admin_panel",
            "password": "adminpassword123"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.get_json()["role"], "admin")

    def test_04_rbac_access_control_on_audit_logs(self):
        """Verify regular users are blocked (403) from Admin Audit Logs while Admins succeed (200)."""
        forbidden = self.client.get("/api/admin/audit-logs?username=tester1")
        self.assertEqual(forbidden.status_code, 403)

        allowed = self.client.get("/api/admin/audit-logs?username=admin_panel")
        self.assertEqual(allowed.status_code, 200)
        data = allowed.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["audit_logs"]), 0)

    def test_05_watchlist_and_favorites_toggle(self):
        """Test adding and removing movies from Watchlist and Favorites."""
        movie_payload = {"id": 550, "title": "Fight Club", "poster": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", "vote_average": 8.4, "media_type": "movie"}
        add_res = self.client.post("/api/user/library/toggle", json={
            "username": "tester1",
            "type": "favorites",
            "movie": movie_payload
        })
        self.assertEqual(add_res.status_code, 200)
        self.assertEqual(add_res.get_json()["action"], "added")

        lib_res = self.client.get("/api/user/library?username=tester1").get_json()
        self.assertEqual(len(lib_res["favorites"]), 1)

    def test_06_not_interested_concept_elimination(self):
        """Test saving 'Not Interested' concepts and keywords."""
        res = self.client.post("/api/user/not_interested", json={
            "username": "tester1",
            "movie": {"id": 9999, "title": "Sample Concept Movie", "vote_average": 5.0},
            "keywords": ["virus", "outbreak", "zombie"]
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["action"], "hidden")

    def test_07_special_category_detection_bl_gl_sports_docs(self):
        """Test NLP classifier for BL, GL, Real-Life Sports, Documentaries, and Anime."""
        self.assertEqual(cinemind_app.detect_special_category("Thai Boys Love BL series"), "BL")
        self.assertEqual(cinemind_app.detect_special_category("Best Girls Love GL series like GAP"), "GL")
        self.assertEqual(cinemind_app.detect_special_category("Real life sports like FIFA and WWE"), "SPORTS")
        self.assertEqual(cinemind_app.detect_special_category("True crime documentary like Jeffrey Dahmer"), "DOC")
        self.assertEqual(cinemind_app.detect_special_category("Japanese anime series"), "ANIME")

    def test_08_animation_blocker_for_sports_and_docs(self):
        """Ensure cartoons/animated movies are detected and excluded from Real-Life Sports & Docs."""
        animated_item = {"id": 1, "title": "Space Jam Cartoon", "genre_ids": [16, 35], "overview": "Animated basketball movie."}
        live_sports_item = {"id": 2, "title": "FIFA Uncovered", "genre_ids": [99], "overview": "Real life football documentary."}
        self.assertTrue(cinemind_app.is_animated_or_cartoon(animated_item))
        self.assertFalse(cinemind_app.is_animated_or_cartoon(live_sports_item))


if __name__ == "__main__":
    unittest.main()
