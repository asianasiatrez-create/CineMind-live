import os
import tempfile
import sqlite3
import importlib
import unittest

class CineMindTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary sqlite database path and point the app at it before importing
        self.db_fd, self.db_path = tempfile.mkstemp(prefix='cinemind_test_', suffix='.db')
        os.close(self.db_fd)
        os.environ['CINEMIND_DB'] = self.db_path

        # Provide admin credentials so seed_admin() will create an admin account on reload
        os.environ['ADMIN_USERNAME'] = 'admin'
        os.environ['ADMIN_PASSWORD'] = 'StrongPassw0rd!'

        # Ensure TMDB/GROQ/OMDB don't block tests; tests will monkeypatch tmdb as needed
        os.environ.setdefault('TMDB_API_KEY', '')
        os.environ.setdefault('GROQ_API_KEY', '')
        os.environ.setdefault('OMDB_API_KEY', '')

        # Import/reload the app module so init_db() and seed_admin() run with our env vars
        import app as cine_app
        importlib.reload(cine_app)
        self.cine_app = cine_app
        self.client = cine_app.app.test_client()

        # Ensure a normal test user exists for RBAC tests
        self.client.post('/api/signup', json={'username': 'testuser', 'password': 'password123'})

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except Exception:
            pass

    def test_tables_exist(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(r[0] for r in cur.fetchall())
        expected = {'users', 'watchlist', 'favorites', 'not_interested', 'interactions', 'audit_logs'}
        for t in expected:
            self.assertIn(t, tables, msg=f"Missing expected table: {t}")
        conn.close()

    def test_signup_and_login(self):
        # Signup a fresh user to verify signup flow
        rv = self.client.post('/api/signup', json={'username': 'testuser2', 'password': 'password123'})
        j = rv.get_json()
        self.assertTrue(j.get('success'), msg=f"Signup failed: {j}")
        # Login
        rv = self.client.post('/api/login', json={'username': 'testuser2', 'password': 'password123'})
        j = rv.get_json()
        self.assertTrue(j.get('success'), msg=f"Login failed: {j}")
        self.assertIn('token', j)

    def test_admin_rbac(self):
        # Login as admin (seed_admin should have created this account)
        rv = self.client.post('/api/login', json={'username': 'admin', 'password': os.environ['ADMIN_PASSWORD']})
        j = rv.get_json()
        self.assertTrue(j.get('success'), msg=f"Admin login failed: {j}")
        admin_token = j.get('token')
        headers = {'Authorization': f'Bearer {admin_token}'}
        # Admin should be allowed to view audit logs
        rv = self.client.get('/api/admin/audit-logs', headers=headers)
        self.assertEqual(rv.status_code, 200)
        j = rv.get_json()
        self.assertTrue(j.get('success'))

        # Normal user must be blocked (403 or 401)
        rv = self.client.post('/api/login', json={'username': 'testuser', 'password': 'password123'})
        j = rv.get_json()
        self.assertTrue(j.get('success'), msg=f"User login failed: {j}")
        user_token = j.get('token')
        rv = self.client.get('/api/admin/audit-logs', headers={'Authorization': f'Bearer {user_token}'})
        self.assertIn(rv.status_code, (401, 403))

    def test_discover_endpoint(self):
        # Monkeypatch the tmdb helper to return a deterministic sample result
        def fake_tmdb(path, **params):
            return {
                'results': [
                    {
                        'id': 123,
                        'poster_path': '/p.jpg',
                        'vote_average': 7.9,
                        'title': 'Fake Movie',
                        'media_type': 'movie',
                        'original_language': 'en',
                        'genre_ids': [18]
                    }
                ],
                'total_pages': 1
            }
        # Replace the tmdb function on the app module
        self.cine_app.tmdb = fake_tmdb

        rv = self.client.get('/api/discover')
        j = rv.get_json()
        self.assertTrue(j.get('success'))
        items = j.get('items') or []
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]['id'], 123)

if __name__ == '__main__':
    unittest.main()
