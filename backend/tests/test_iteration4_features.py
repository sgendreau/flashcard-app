"""
Backend API Tests for Iteration 4 Features
Tests: Daily Rewards System, Private Classes, Grade-Locked Classes
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


class TestDailyRewards:
    """Daily rewards system tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_daily_reward_status(self, auth_token):
        """Test GET /api/rewards/daily returns reward status"""
        response = requests.get(f"{BASE_URL}/api/rewards/daily", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get daily reward failed: {response.text}"
        
        data = response.json()
        assert "already_claimed" in data
        assert "can_claim" in data
        assert "reward_day" in data
        assert "reward_xp" in data
        assert "studied_today" in data
        assert "all_rewards" in data
        
        # Verify reward_day is 1-7
        assert 1 <= data["reward_day"] <= 7, f"reward_day should be 1-7, got {data['reward_day']}"
        
        # Verify all_rewards has 7 days
        assert len(data["all_rewards"]) == 7, "Should have 7 days of rewards"
        
        print(f"✓ Daily reward status: Day {data['reward_day']}, {data['reward_xp']} XP, can_claim={data['can_claim']}")

    def test_claim_daily_reward_without_studying(self, auth_token):
        """Test POST /api/rewards/claim fails if user hasn't studied today"""
        # First check if already claimed today
        status_response = requests.get(f"{BASE_URL}/api/rewards/daily", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        status = status_response.json()
        
        if status["already_claimed"]:
            print("✓ Reward already claimed today (skipping claim test)")
            pytest.skip("Reward already claimed today")
        
        if status["studied_today"]:
            print("✓ User already studied today (can claim)")
            # Try to claim
            claim_response = requests.post(f"{BASE_URL}/api/rewards/claim", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            if claim_response.status_code == 200:
                data = claim_response.json()
                assert "xp_earned" in data
                assert "reward_day" in data
                assert "total_xp" in data
                print(f"✓ Claimed reward: +{data['xp_earned']} XP, now day {data['reward_day']}")
            else:
                print(f"✓ Claim failed as expected: {claim_response.json()}")
        else:
            # Try to claim without studying
            claim_response = requests.post(f"{BASE_URL}/api/rewards/claim", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            assert claim_response.status_code == 400, "Should fail if not studied today"
            print("✓ Claim rejected when user hasn't studied today")

    def test_daily_reward_requires_auth(self):
        """Test GET /api/rewards/daily requires authentication"""
        response = requests.get(f"{BASE_URL}/api/rewards/daily")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Daily reward endpoint requires authentication")


class TestPrivateClasses:
    """Private class tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    @pytest.fixture
    def student_token(self):
        """Create a test student"""
        timestamp = int(time.time())
        test_email = f"test_private_class_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student Private",
            "email": test_email,
            "password": "test1234"
        })
        if response.status_code != 200:
            pytest.skip(f"Student registration failed: {response.text}")
        return response.json()["access_token"]

    def test_create_private_class(self, auth_token):
        """Test POST /api/classes with is_private=true"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": f"Private Class {timestamp}",
                "is_private": True,
                "locked_grade": None
            }
        )
        assert response.status_code == 200, f"Create private class failed: {response.text}"
        
        data = response.json()
        assert "class" in data
        cls = data["class"]
        assert cls["is_private"] is True, "is_private should be True"
        assert cls["locked_grade"] is None
        
        print(f"✓ Private class created: {cls['name']}, code={cls['code']}")

    def test_create_public_class(self, auth_token):
        """Test POST /api/classes with is_private=false (default)"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": f"Public Class {timestamp}",
                "is_private": False
            }
        )
        assert response.status_code == 200, f"Create public class failed: {response.text}"
        
        data = response.json()
        cls = data["class"]
        assert cls["is_private"] is False, "is_private should be False"
        
        print(f"✓ Public class created: {cls['name']}")


class TestGradeLockedClasses:
    """Grade-locked class tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    @pytest.fixture
    def student_terminale_token(self):
        """Create a test student with grade_level=terminale"""
        timestamp = int(time.time())
        test_email = f"test_terminale_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student Terminale",
            "email": test_email,
            "password": "test1234"
        })
        if response.status_code != 200:
            pytest.skip(f"Student registration failed: {response.text}")
        
        token = response.json()["access_token"]
        
        # Set grade to terminale
        requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {token}"},
            json={"grade_level": "terminale"}
        )
        
        return token

    @pytest.fixture
    def student_6eme_token(self):
        """Create a test student with grade_level=6eme"""
        timestamp = int(time.time())
        test_email = f"test_6eme_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student 6eme",
            "email": test_email,
            "password": "test1234"
        })
        if response.status_code != 200:
            pytest.skip(f"Student registration failed: {response.text}")
        
        token = response.json()["access_token"]
        
        # Set grade to 6eme
        requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {token}"},
            json={"grade_level": "6eme"}
        )
        
        return token

    def test_create_grade_locked_class(self, auth_token):
        """Test POST /api/classes with locked_grade"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": f"Terminale Only Class {timestamp}",
                "is_private": False,
                "locked_grade": "terminale"
            }
        )
        assert response.status_code == 200, f"Create grade-locked class failed: {response.text}"
        
        data = response.json()
        cls = data["class"]
        assert cls["locked_grade"] == "terminale", "locked_grade should be 'terminale'"
        
        print(f"✓ Grade-locked class created: {cls['name']}, locked to {cls['locked_grade']}")

    def test_join_grade_locked_class_matching_grade(self, auth_token, student_terminale_token):
        """Test joining grade-locked class with matching grade"""
        # Create terminale-locked class
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Terminale Lock Test",
                "locked_grade": "terminale"
            }
        )
        class_code = create_response.json()["class"]["code"]
        
        # Join with terminale student
        join_response = requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_terminale_token}"},
            json={"code": class_code}
        )
        assert join_response.status_code == 200, f"Join should succeed with matching grade: {join_response.text}"
        
        data = join_response.json()
        assert len(data["class"]["members"]) == 2, "Should have 2 members after join"
        
        print(f"✓ Terminale student joined terminale-locked class successfully")

    def test_join_grade_locked_class_mismatched_grade(self, auth_token, student_6eme_token):
        """Test joining grade-locked class with mismatched grade"""
        # Create terminale-locked class
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Terminale Lock Reject Test",
                "locked_grade": "terminale"
            }
        )
        class_code = create_response.json()["class"]["code"]
        
        # Try to join with 6eme student
        join_response = requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_6eme_token}"},
            json={"code": class_code}
        )
        assert join_response.status_code == 403, f"Join should fail with mismatched grade, got {join_response.status_code}"
        
        error_data = join_response.json()
        assert "terminale" in error_data.get("detail", "").lower(), "Error should mention grade requirement"
        
        print(f"✓ 6eme student rejected from terminale-locked class: {error_data['detail']}")

    def test_join_unlocked_class_any_grade(self, auth_token, student_6eme_token):
        """Test joining unlocked class works with any grade"""
        # Create unlocked class
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Unlocked Class Test",
                "locked_grade": None
            }
        )
        class_code = create_response.json()["class"]["code"]
        
        # Join with 6eme student
        join_response = requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_6eme_token}"},
            json={"code": class_code}
        )
        assert join_response.status_code == 200, f"Join should succeed for unlocked class: {join_response.text}"
        
        print(f"✓ 6eme student joined unlocked class successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
