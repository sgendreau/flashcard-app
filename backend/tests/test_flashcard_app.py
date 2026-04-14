"""
Backend API Tests for Flashcard App
Tests: Auth (login, register, logout), Subjects, Study Session, Flashcards, Progress
"""
import pytest
import requests
import os
import time

# Read from frontend .env file
def get_backend_url():
    env_path = '/app/frontend/.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    return line.split('=', 1)[1].strip().rstrip('/')
    return ''

BASE_URL = get_backend_url()

class TestAuth:
    """Authentication endpoint tests"""

    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "refresh_token" in data, "Missing refresh_token"
        assert "user" in data, "Missing user object"
        assert data["user"]["email"] == "admin@flashcards.com"
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Should return 401 for wrong password"
        print("✓ Invalid credentials rejected correctly")

    def test_register_new_user(self):
        """Test user registration"""
        timestamp = int(time.time())
        test_email = f"test_student_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student",
            "email": test_email,
            "password": "test1234"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == test_email
        assert data["user"]["role"] == "student"
        assert data["user"]["xp"] == 0
        assert data["user"]["level"] == 1
        print(f"✓ User registration successful: {test_email}")

    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Admin Duplicate",
            "email": "admin@flashcards.com",
            "password": "test123"
        })
        assert response.status_code == 400, "Should reject duplicate email"
        print("✓ Duplicate email rejected correctly")

    def test_get_me_with_token(self):
        """Test /auth/me endpoint with valid token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Get me failed: {response.text}"
        
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "admin@flashcards.com"
        print("✓ Get current user successful")

    def test_get_me_without_token(self):
        """Test /auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Unauthenticated request rejected")


class TestSubjects:
    """Subjects endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_subjects_authenticated(self, auth_token):
        """Test getting all subjects with authentication"""
        response = requests.get(f"{BASE_URL}/api/subjects", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get subjects failed: {response.text}"
        
        data = response.json()
        assert "subjects" in data
        subjects = data["subjects"]
        assert len(subjects) == 9, f"Expected 9 subjects, got {len(subjects)}"
        
        # Verify subject structure
        subject_ids = [s["id"] for s in subjects]
        expected_ids = ["maths", "francais", "histoire_geo", "svt", "physique_chimie", 
                       "anglais", "philosophie", "ses", "espagnol"]
        for expected_id in expected_ids:
            assert expected_id in subject_ids, f"Missing subject: {expected_id}"
        
        # Check card counts
        for subject in subjects:
            assert "card_count" in subject, f"Missing card_count for {subject['id']}"
            assert subject["card_count"] >= 0
        
        print(f"✓ Got {len(subjects)} subjects with card counts")

    def test_get_subjects_unauthenticated(self):
        """Test subjects endpoint without auth"""
        response = requests.get(f"{BASE_URL}/api/subjects")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Subjects endpoint requires auth")


class TestFlashcards:
    """Flashcards endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_flashcards_for_subject(self, auth_token):
        """Test getting flashcards for a specific subject"""
        response = requests.get(f"{BASE_URL}/api/flashcards/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get flashcards failed: {response.text}"
        
        data = response.json()
        assert "flashcards" in data
        cards = data["flashcards"]
        assert len(cards) >= 5, f"Expected at least 5 cards for maths, got {len(cards)}"
        
        # Verify card structure
        for card in cards:
            assert "id" in card
            assert "subject_id" in card
            assert "question" in card
            assert "answer" in card
            assert card["subject_id"] == "maths"
        
        print(f"✓ Got {len(cards)} flashcards for maths")

    def test_create_flashcard(self, auth_token):
        """Test creating a new flashcard"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/flashcards", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "subject_id": "maths",
                "question": f"Test Question {timestamp}",
                "answer": f"Test Answer {timestamp}"
            }
        )
        assert response.status_code == 200, f"Create flashcard failed: {response.text}"
        
        data = response.json()
        assert "flashcard" in data
        card = data["flashcard"]
        assert card["question"] == f"Test Question {timestamp}"
        assert card["answer"] == f"Test Answer {timestamp}"
        assert card["subject_id"] == "maths"
        
        # Verify persistence by getting the card
        get_response = requests.get(f"{BASE_URL}/api/flashcards/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        cards = get_response.json()["flashcards"]
        created_card = next((c for c in cards if c["id"] == card["id"]), None)
        assert created_card is not None, "Created card not found in GET request"
        
        print(f"✓ Created flashcard and verified persistence")


class TestStudySession:
    """Study session endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_start_study_session(self, auth_token):
        """Test starting a study session"""
        response = requests.get(f"{BASE_URL}/api/study/start/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Start study failed: {response.text}"
        
        data = response.json()
        assert "session_cards" in data
        assert "total" in data
        
        cards = data["session_cards"]
        assert len(cards) > 0, "Should return at least one card"
        assert len(cards) <= 15, "Should cap at 15 cards"
        
        # Verify card structure
        for card in cards:
            assert "card_id" in card
            assert "question" in card
            assert "answer" in card
            assert "show_side" in card
            assert "box" in card
            assert card["show_side"] in ["question", "answer"]
            assert card["box"] in [1, 2, 3]
        
        print(f"✓ Started study session with {len(cards)} cards")
        return cards

    def test_submit_study_results(self, auth_token):
        """Test submitting study session results"""
        # Start session first
        start_response = requests.get(f"{BASE_URL}/api/study/start/francais", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        cards = start_response.json()["session_cards"]
        
        # Submit results (mark all as correct)
        results = [{"card_id": card["card_id"], "is_correct": True} for card in cards]
        submit_response = requests.post(f"{BASE_URL}/api/study/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "subject_id": "francais",
                "results": results
            }
        )
        assert submit_response.status_code == 200, f"Submit failed: {submit_response.text}"
        
        data = submit_response.json()
        assert "total_cards" in data
        assert "correct_count" in data
        assert "incorrect_count" in data
        assert "percentage" in data
        assert "xp_earned" in data
        assert "new_badges" in data
        assert "cards_to_review" in data
        assert "streak_count" in data
        assert "new_level" in data
        assert "total_xp" in data
        
        assert data["total_cards"] == len(cards)
        assert data["correct_count"] == len(cards)
        assert data["percentage"] == 100
        assert data["xp_earned"] > 0
        
        print(f"✓ Submitted study results: {data['percentage']}% correct, {data['xp_earned']} XP earned")

    def test_submit_mixed_results(self, auth_token):
        """Test submitting mixed correct/incorrect results"""
        start_response = requests.get(f"{BASE_URL}/api/study/start/svt", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        cards = start_response.json()["session_cards"]
        
        # Mark half correct, half incorrect
        results = []
        for i, card in enumerate(cards):
            results.append({"card_id": card["card_id"], "is_correct": i % 2 == 0})
        
        submit_response = requests.post(f"{BASE_URL}/api/study/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "subject_id": "svt",
                "results": results
            }
        )
        assert submit_response.status_code == 200
        
        data = submit_response.json()
        assert data["incorrect_count"] > 0
        assert len(data["cards_to_review"]) == data["incorrect_count"]
        
        print(f"✓ Mixed results: {data['correct_count']}/{data['total_cards']} correct")


class TestProgress:
    """Progress stats endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_progress_stats(self, auth_token):
        """Test getting user progress statistics"""
        response = requests.get(f"{BASE_URL}/api/progress/stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get progress failed: {response.text}"
        
        data = response.json()
        assert "sessions" in data
        assert "box_counts" in data
        assert "total_sessions" in data
        
        box_counts = data["box_counts"]
        assert "box_1" in box_counts
        assert "box_2" in box_counts
        assert "box_3" in box_counts
        
        print(f"✓ Progress stats: {data['total_sessions']} sessions, Box counts: {box_counts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
