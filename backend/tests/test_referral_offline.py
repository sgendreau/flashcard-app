"""
Backend API Tests for Referral System and Offline Mode
Tests: Referral code generation, referral XP bonus, referral stats, sync status
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


class TestReferralSystem:
    """Referral system tests"""

    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]

    def test_admin_has_referral_code(self, admin_token):
        """Test that admin user has a referral code"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        
        user = response.json()["user"]
        assert "referral_code" in user
        assert user["referral_code"].startswith("FC"), "Referral code should start with FC"
        assert len(user["referral_code"]) == 7, "Referral code should be FC + 5 chars = 7 total"
        
        print(f"✓ Admin has referral code: {user['referral_code']}")

    def test_get_referral_stats(self, admin_token):
        """Test GET /api/referral/stats returns referral data"""
        response = requests.get(f"{BASE_URL}/api/referral/stats", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get referral stats failed: {response.text}"
        
        data = response.json()
        assert "referral_code" in data
        assert "referral_count" in data
        assert "xp_earned_from_referrals" in data
        assert "referred_users" in data
        
        assert data["referral_code"].startswith("FC")
        assert isinstance(data["referral_count"], int)
        assert data["xp_earned_from_referrals"] == data["referral_count"] * 100
        assert isinstance(data["referred_users"], list)
        
        print(f"✓ Referral stats: code={data['referral_code']}, count={data['referral_count']}, xp={data['xp_earned_from_referrals']}")

    def test_register_without_referral_code(self):
        """Test registration without referral code gives 0 XP"""
        timestamp = int(time.time())
        test_email = f"test_no_ref_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test No Referral",
            "email": test_email,
            "password": "test1234"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "user" in data
        user = data["user"]
        assert user["xp"] == 0, "User without referral should have 0 XP"
        assert "referral_code" in user
        assert user["referral_code"].startswith("FC"), "New user should get their own referral code"
        
        print(f"✓ User registered without referral code: XP={user['xp']}, own code={user['referral_code']}")

    def test_register_with_valid_referral_code(self, admin_token):
        """Test registration with valid referral code gives 100 XP to both users"""
        # Get admin's referral code and current XP
        admin_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        admin_user = admin_response.json()["user"]
        admin_referral_code = admin_user["referral_code"]
        admin_xp_before = admin_user["xp"]
        
        # Register new user with admin's referral code
        timestamp = int(time.time())
        test_email = f"test_with_ref_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test With Referral",
            "email": test_email,
            "password": "test1234",
            "referral_code": admin_referral_code
        })
        assert response.status_code == 200, f"Registration with referral failed: {response.text}"
        
        data = response.json()
        new_user = data["user"]
        assert new_user["xp"] == 100, "New user with referral should have 100 XP"
        
        # Verify admin got 100 XP bonus
        admin_response_after = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        admin_user_after = admin_response_after.json()["user"]
        admin_xp_after = admin_user_after["xp"]
        
        assert admin_xp_after == admin_xp_before + 100, f"Admin should get 100 XP bonus. Before: {admin_xp_before}, After: {admin_xp_after}"
        
        # Verify referral stats updated
        stats_response = requests.get(f"{BASE_URL}/api/referral/stats", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        stats = stats_response.json()
        
        print(f"✓ Referral successful: New user XP=100, Admin XP increased by 100 (now {admin_xp_after}), Referral count={stats['referral_count']}")

    def test_register_with_invalid_referral_code(self):
        """Test registration with invalid referral code still works but no bonus"""
        timestamp = int(time.time())
        test_email = f"test_invalid_ref_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Invalid Referral",
            "email": test_email,
            "password": "test1234",
            "referral_code": "INVALID123"
        })
        assert response.status_code == 200, f"Registration should succeed even with invalid referral: {response.text}"
        
        data = response.json()
        user = data["user"]
        assert user["xp"] == 0, "User with invalid referral should have 0 XP"
        
        print(f"✓ Registration with invalid referral code succeeded with 0 XP")

    def test_referral_stats_requires_auth(self):
        """Test GET /api/referral/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/stats")
        assert response.status_code == 401, "Should require authentication"
        
        print("✓ Referral stats endpoint requires authentication")


class TestSyncStatus:
    """Sync status tests (for offline mode)"""

    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_get_sync_status(self, admin_token):
        """Test GET /api/sync/status returns sync data"""
        response = requests.get(f"{BASE_URL}/api/sync/status", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Get sync status failed: {response.text}"
        
        data = response.json()
        assert "synced" in data
        assert "card_progress_count" in data
        assert "session_count" in data
        assert "server_time" in data
        
        assert isinstance(data["synced"], bool)
        assert isinstance(data["card_progress_count"], int)
        assert isinstance(data["session_count"], int)
        assert isinstance(data["server_time"], str)
        
        # last_activity is optional (only if sessions exist)
        if data["session_count"] > 0:
            assert "last_activity" in data
        
        print(f"✓ Sync status: synced={data['synced']}, sessions={data['session_count']}, progress={data['card_progress_count']}")

    def test_sync_status_requires_auth(self):
        """Test GET /api/sync/status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/sync/status")
        assert response.status_code == 401, "Should require authentication"
        
        print("✓ Sync status endpoint requires authentication")


class TestRegressionPreviousFeatures:
    """Regression tests to ensure previous features still work"""

    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_login_still_works(self):
        """Test POST /api/auth/login still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        
        print("✓ Login endpoint still works")

    def test_get_subjects_still_works(self, admin_token):
        """Test GET /api/subjects still works"""
        response = requests.get(f"{BASE_URL}/api/subjects", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "subjects" in data
        assert len(data["subjects"]) > 0
        
        print(f"✓ Get subjects endpoint still works ({len(data['subjects'])} subjects)")

    def test_daily_rewards_still_works(self, admin_token):
        """Test GET /api/rewards/daily still works"""
        response = requests.get(f"{BASE_URL}/api/rewards/daily", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "reward_day" in data
        assert "all_rewards" in data
        
        print(f"✓ Daily rewards endpoint still works (day {data['reward_day']})")

    def test_challenges_still_works(self, admin_token):
        """Test GET /api/challenges still works"""
        response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "challenges" in data
        
        print(f"✓ Challenges endpoint still works ({len(data['challenges'])} challenges)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
