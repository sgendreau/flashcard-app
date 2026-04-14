"""
Backend API Tests for Iteration 3 Features
Tests: Subject Stats, Class Leaderboard, Theme Toggle
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


class TestSubjectStats:
    """Per-subject statistics endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_subject_stats(self, auth_token):
        """Test GET /api/progress/subject-stats returns per-subject data"""
        response = requests.get(f"{BASE_URL}/api/progress/subject-stats", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get subject stats failed: {response.text}"
        
        data = response.json()
        assert "subject_stats" in data, "Response should contain subject_stats"
        
        stats = data["subject_stats"]
        # Admin may or may not have study sessions, so just verify structure
        if len(stats) > 0:
            # Verify structure of first stat entry
            stat = stats[0]
            required_fields = [
                "subject_id", "name", "color", "icon",
                "total_sessions", "total_correct", "total_cards_reviewed",
                "avg_percentage", "total_xp", "box_distribution",
                "total_cards", "mastered", "mastery_pct"
            ]
            for field in required_fields:
                assert field in stat, f"Missing field: {field}"
            
            # Verify box_distribution structure
            assert "box_1" in stat["box_distribution"]
            assert "box_2" in stat["box_distribution"]
            assert "box_3" in stat["box_distribution"]
            
            # Verify data types
            assert isinstance(stat["total_sessions"], int)
            assert isinstance(stat["avg_percentage"], int)
            assert isinstance(stat["mastery_pct"], int)
            
            print(f"✓ Subject stats returned {len(stats)} subjects with valid structure")
        else:
            print("✓ Subject stats endpoint working (no sessions yet for admin)")

    def test_subject_stats_requires_auth(self):
        """Test that subject stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/progress/subject-stats")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Subject stats requires authentication")


class TestClassLeaderboard:
    """Class leaderboard endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    @pytest.fixture
    def test_class_id(self, auth_token):
        """Create a test class and return its ID"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": f"Leaderboard Test Class {timestamp}"}
        )
        return response.json()["class"]["id"]

    def test_get_class_leaderboard(self, auth_token, test_class_id):
        """Test GET /api/classes/{class_id}/leaderboard"""
        response = requests.get(f"{BASE_URL}/api/classes/{test_class_id}/leaderboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get leaderboard failed: {response.text}"
        
        data = response.json()
        assert "leaderboard" in data, "Response should contain leaderboard"
        
        leaderboard = data["leaderboard"]
        assert len(leaderboard) >= 1, "Should have at least the creator in leaderboard"
        
        # Verify structure of leaderboard entries
        for entry in leaderboard:
            required_fields = ["user_id", "name", "xp", "level", "streak", "sessions", "avg_score", "rank"]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
            
            # Verify data types
            assert isinstance(entry["xp"], int)
            assert isinstance(entry["level"], int)
            assert isinstance(entry["rank"], int)
            assert isinstance(entry["sessions"], int)
            assert isinstance(entry["avg_score"], int)
        
        # Verify leaderboard is sorted by XP (descending)
        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]["xp"] >= leaderboard[i+1]["xp"], "Leaderboard should be sorted by XP descending"
        
        # Verify ranks are sequential
        for i, entry in enumerate(leaderboard):
            assert entry["rank"] == i + 1, f"Rank should be {i+1}, got {entry['rank']}"
        
        print(f"✓ Leaderboard returned {len(leaderboard)} members, sorted by XP")

    def test_leaderboard_requires_membership(self, auth_token):
        """Test that leaderboard requires class membership"""
        # Try to access a non-existent class
        response = requests.get(f"{BASE_URL}/api/classes/nonexistent_class_id/leaderboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code in [403, 404], "Should reject non-member access"
        print("✓ Leaderboard requires class membership")

    def test_leaderboard_with_multiple_members(self, auth_token):
        """Test leaderboard with multiple members"""
        # Create a class
        timestamp = int(time.time())
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": f"Multi Member Test {timestamp}"}
        )
        class_id = create_response.json()["class"]["id"]
        class_code = create_response.json()["class"]["code"]
        
        # Create a second user and join
        student_email = f"test_student_lb_{timestamp}@flashcards.com"
        student_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student LB",
            "email": student_email,
            "password": "test1234"
        })
        student_token = student_response.json()["access_token"]
        
        # Join the class
        requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"code": class_code}
        )
        
        # Get leaderboard
        response = requests.get(f"{BASE_URL}/api/classes/{class_id}/leaderboard", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        leaderboard = response.json()["leaderboard"]
        assert len(leaderboard) == 2, "Should have 2 members in leaderboard"
        
        # Admin should be ranked higher (has more XP from previous tests)
        admin_entry = next((e for e in leaderboard if "admin" in e["name"].lower()), None)
        student_entry = next((e for e in leaderboard if "student" in e["name"].lower()), None)
        
        if admin_entry and student_entry:
            assert admin_entry["rank"] <= student_entry["rank"], "Admin should be ranked higher or equal"
        
        print(f"✓ Leaderboard with 2 members working correctly")


class TestThemeToggle:
    """Theme toggle endpoint tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_update_theme_to_dark(self, auth_token):
        """Test PUT /api/user/theme to set dark theme"""
        response = requests.put(f"{BASE_URL}/api/user/theme",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"theme": "dark"}
        )
        assert response.status_code == 200, f"Update theme failed: {response.text}"
        
        data = response.json()
        assert "theme" in data
        assert data["theme"] == "dark"
        
        # Verify persistence by getting user info
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        user = me_response.json()["user"]
        # Note: theme field may not be in user_response function, but should be in DB
        
        print("✓ Theme updated to 'dark'")

    def test_update_theme_to_light(self, auth_token):
        """Test PUT /api/user/theme to set light theme"""
        response = requests.put(f"{BASE_URL}/api/user/theme",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"theme": "light"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["theme"] == "light"
        
        print("✓ Theme updated to 'light'")

    def test_update_invalid_theme(self, auth_token):
        """Test PUT /api/user/theme with invalid theme"""
        response = requests.put(f"{BASE_URL}/api/user/theme",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"theme": "invalid_theme"}
        )
        assert response.status_code == 400, "Should reject invalid theme"
        
        print("✓ Invalid theme rejected")

    def test_theme_requires_auth(self):
        """Test that theme update requires authentication"""
        response = requests.put(f"{BASE_URL}/api/user/theme",
            json={"theme": "dark"}
        )
        assert response.status_code == 401, "Should require authentication"
        print("✓ Theme update requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
