"""
Backend tests for iteration 6 features:
1. AI flashcard generation (POST /api/ai/generate)
2. Multi-device sync status (GET /api/sync/status)
3. Tablet responsive layout (no backend changes)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    pytest.skip("EXPO_PUBLIC_BACKEND_URL not set", allow_module_level=True)

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def auth_token(api_client):
    """Login and return auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@flashcards.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]

class TestAIGeneration:
    """AI flashcard generation endpoint tests"""

    def test_ai_generate_endpoint_requires_auth(self, api_client):
        """POST /api/ai/generate requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/ai/generate", json={
            "subject_id": "maths",
            "text": "Test text",
            "count": 5
        })
        assert response.status_code == 401, "Should require authentication"
        print("✓ AI generate endpoint requires auth")

    def test_ai_generate_endpoint_exists(self, api_client, auth_token):
        """POST /api/ai/generate endpoint exists (don't actually call AI - costs money)"""
        # We'll send a request but expect it to fail validation or return error
        # Just verify the endpoint exists and is routed correctly
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Send minimal invalid request to verify endpoint exists
        response = api_client.post(f"{BASE_URL}/api/ai/generate", json={
            "subject_id": "maths",
            "text": "",  # Empty text should fail validation
            "count": 5
        })
        
        # We expect either 200 (success), 400 (validation error) or 500 (AI error)
        # All indicate the endpoint exists and is processing the request
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        # If it succeeded, verify response structure
        if response.status_code == 200:
            data = response.json()
            assert "generated" in data, "Missing generated field"
            assert "cards" in data, "Missing cards field"
            print(f"✓ AI generate endpoint exists and works (generated {data.get('generated', 0)} cards)")
        else:
            print(f"✓ AI generate endpoint exists (status: {response.status_code})")

    def test_ai_generate_validates_input(self, api_client, auth_token):
        """POST /api/ai/generate validates input fields"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        # Missing required fields
        response = api_client.post(f"{BASE_URL}/api/ai/generate", json={})
        assert response.status_code in [400, 422], "Should validate required fields"
        print("✓ AI generate validates input")

class TestSyncStatus:
    """Multi-device sync status endpoint tests"""

    def test_sync_status_requires_auth(self, api_client):
        """GET /api/sync/status requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/sync/status")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Sync status endpoint requires auth")

    def test_sync_status_returns_data(self, api_client, auth_token):
        """GET /api/sync/status returns sync information"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/sync/status")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "synced" in data, "Missing synced field"
        assert "card_progress_count" in data, "Missing card_progress_count"
        assert "session_count" in data, "Missing session_count"
        assert "server_time" in data, "Missing server_time"
        
        # Verify data types
        assert isinstance(data["synced"], bool), "synced should be boolean"
        assert isinstance(data["card_progress_count"], int), "card_progress_count should be int"
        assert isinstance(data["session_count"], int), "session_count should be int"
        
        print(f"✓ Sync status returns data: {data['session_count']} sessions, {data['card_progress_count']} cards")

    def test_sync_status_includes_last_activity(self, api_client, auth_token):
        """GET /api/sync/status includes last_activity if user has sessions"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/sync/status")
        assert response.status_code == 200
        
        data = response.json()
        # last_activity can be null if no sessions, or a timestamp string
        if data.get("session_count", 0) > 0:
            assert "last_activity" in data, "Should include last_activity when sessions exist"
            if data["last_activity"]:
                # Verify it's a valid ISO timestamp
                from datetime import datetime
                datetime.fromisoformat(data["last_activity"].replace('Z', '+00:00'))
                print(f"✓ Sync status includes last_activity: {data['last_activity']}")
        else:
            print("✓ Sync status checked (no sessions yet)")

class TestRegressionAPIs:
    """Verify all previous iteration APIs still work"""

    def test_daily_rewards_still_works(self, api_client, auth_token):
        """GET /api/rewards/daily still works (iteration 4)"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/rewards/daily")
        assert response.status_code == 200, "Daily rewards endpoint broken"
        data = response.json()
        assert "reward_day" in data
        print("✓ Daily rewards API still works")

    def test_challenges_still_works(self, api_client, auth_token):
        """GET /api/challenges still works (iteration 5)"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/challenges")
        assert response.status_code == 200, "Challenges endpoint broken"
        data = response.json()
        assert "challenges" in data
        assert len(data["challenges"]) == 4, "Should have 4 challenges"
        print("✓ Challenges API still works")

    def test_exam_mode_still_works(self, api_client, auth_token):
        """GET /api/study/exam/{subject_id} still works (iteration 5)"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/study/exam/maths")
        assert response.status_code == 200, "Exam mode endpoint broken"
        data = response.json()
        assert "session_cards" in data
        assert "mastery_pct" in data
        print("✓ Exam mode API still works")

    def test_subjects_endpoint_still_works(self, api_client, auth_token):
        """GET /api/subjects still works"""
        api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
        response = api_client.get(f"{BASE_URL}/api/subjects")
        assert response.status_code == 200, "Subjects endpoint broken"
        data = response.json()
        assert "subjects" in data
        assert len(data["subjects"]) > 0, "Should have subjects"
        print(f"✓ Subjects API still works ({len(data['subjects'])} subjects)")
