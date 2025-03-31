import unittest
from app import app, db
from flask import session

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing forms
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_homepage(self):
        """Test that the homepage loads correctly."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for expected text; adjust as needed
        self.assertIn(b"movie", response.data.lower())

    def test_signup_page(self):
        """Test that the signup page loads correctly."""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        # Update the assertion to look for "sign up" (with a space)
        self.assertIn(b"sign up", response.data.lower())

    def test_login_page(self):
        """Test that the login page loads correctly."""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.data.lower())

if __name__ == '__main__':
    unittest.main()
