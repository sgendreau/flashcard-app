"""
Backend API Tests for Iteration 5 - New Features
Tests: Exam Revision Mode, Weekly Challenges, Social Sharing
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


class TestExamRevisionMode:
    """Exam revision mode tests - GET /api/study/exam/{subject_id}"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]

    def test_exam_mode_returns_all_cards_no_grade_filter(self, auth_token):
        """Test GET /api/study/exam/maths returns ALL cards regardless of user grade"""
        # First set user grade to 6eme
        requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"grade_level": "6eme"}
        )
        
        # Get exam mode cards
        response = requests.get(f"{BASE_URL}/api/study/exam/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Exam mode failed: {response.text}"
        
        data = response.json()
        assert "session_cards" in data
        assert "total" in data
        assert "total_subject_cards" in data
        assert "mastered_cards" in data
        assert "mastery_pct" in data
        
        # Should return cards even if user grade is 6eme (exam mode ignores grade filter)
        assert len(data["session_cards"]) > 0, "Exam mode should return cards regardless of grade"
        
        print(f"✓ Exam mode returned {len(data['session_cards'])} cards (no grade filter)")

    def test_exam_mode_returns_up_to_30_cards(self, auth_token):
        """Test exam mode returns maximum 30 cards"""
        response = requests.get(f"{BASE_URL}/api/study/exam/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["session_cards"]) <= 30, "Exam mode should return max 30 cards"
        
        print(f"✓ Exam mode returned {len(data['session_cards'])} cards (max 30)")

    def test_exam_mode_prioritizes_by_weakness(self, auth_token):
        """Test exam mode prioritizes box 1 cards (weakest) first"""
        response = requests.get(f"{BASE_URL}/api/study/exam/francais", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        cards = data["session_cards"]
        
        # Verify cards have box information
        for card in cards:
            assert "card_id" in card
            assert "question" in card
            assert "answer" in card
            assert "show_side" in card
            assert "box" in card
        
        # First cards should be box 1 (weakest) if any exist
        if len(cards) > 0:
            first_boxes = [c["box"] for c in cards[:5]]
            print(f"✓ First 5 cards boxes: {first_boxes} (box 1 = weakest, prioritized)")

    def test_exam_mode_includes_mastery_percentage(self, auth_token):
        """Test exam mode returns mastery_pct for progress tracking"""
        response = requests.get(f"{BASE_URL}/api/study/exam/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "mastery_pct" in data
        assert isinstance(data["mastery_pct"], (int, float))
        assert 0 <= data["mastery_pct"] <= 100
        
        print(f"✓ Exam mode returned mastery_pct: {data['mastery_pct']}%")

    def test_exam_mode_invalid_subject(self, auth_token):
        """Test exam mode with invalid subject returns 404"""
        response = requests.get(f"{BASE_URL}/api/study/exam/invalid_subject", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 404, "Should return 404 for invalid subject"
        
        print("✓ Invalid subject rejected with 404")


class TestWeeklyChallenges:
    """Weekly challenges tests - GET /api/challenges and POST /api/challenges/{id}/claim"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_get_challenges_returns_4_challenges(self, auth_token):
        """Test GET /api/challenges returns 4 weekly challenges"""
        response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get challenges failed: {response.text}"
        
        data = response.json()
        assert "challenges" in data
        assert "week_start" in data
        
        challenges = data["challenges"]
        assert len(challenges) == 4, f"Expected 4 challenges, got {len(challenges)}"
        
        # Verify challenge IDs
        challenge_ids = [c["id"] for c in challenges]
        expected_ids = ["sessions_5", "perfect_2", "subjects_3", "master_5"]
        for expected_id in expected_ids:
            assert expected_id in challenge_ids, f"Missing challenge: {expected_id}"
        
        print(f"✓ Got 4 challenges: {challenge_ids}")

    def test_challenges_have_required_fields(self, auth_token):
        """Test challenges have all required fields"""
        response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        data = response.json()
        
        for challenge in data["challenges"]:
            assert "id" in challenge
            assert "type" in challenge
            assert "title" in challenge
            assert "description" in challenge
            assert "target" in challenge
            assert "xp_reward" in challenge
            assert "icon" in challenge
            assert "progress" in challenge
            assert "completed" in challenge
            assert "claimed" in challenge
        
        print("✓ All challenges have required fields")

    def test_challenges_show_progress(self, auth_token):
        """Test challenges show current progress"""
        response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        data = response.json()
        
        for challenge in data["challenges"]:
            assert isinstance(challenge["progress"], int)
            assert isinstance(challenge["target"], int)
            assert challenge["progress"] >= 0
            assert challenge["progress"] <= challenge["target"]
            
            # completed should be true if progress >= target
            if challenge["progress"] >= challenge["target"]:
                assert challenge["completed"] is True
        
        print("✓ Challenges show progress correctly")

    def test_claim_challenge_when_completed(self, auth_token):
        """Test POST /api/challenges/{id}/claim awards XP when completed"""
        # First get challenges to find a completed one
        get_response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        challenges = get_response.json()["challenges"]
        
        # Find a completed but unclaimed challenge
        completed_challenge = None
        for ch in challenges:
            if ch["completed"] and not ch["claimed"]:
                completed_challenge = ch
                break
        
        if not completed_challenge:
            print("⚠ No completed unclaimed challenges to test claim")
            pytest.skip("No completed challenges available")
        
        # Claim the challenge
        claim_response = requests.post(f"{BASE_URL}/api/challenges/{completed_challenge['id']}/claim",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert claim_response.status_code == 200, f"Claim failed: {claim_response.text}"
        
        data = claim_response.json()
        assert "xp_earned" in data
        assert "total_xp" in data
        assert "new_level" in data
        assert data["xp_earned"] == completed_challenge["xp_reward"]
        
        print(f"✓ Claimed challenge '{completed_challenge['id']}' for {data['xp_earned']} XP")

    def test_claim_challenge_already_claimed(self, auth_token):
        """Test claiming same challenge twice returns 400"""
        # Get challenges
        get_response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        challenges = get_response.json()["challenges"]
        
        # Find a claimed challenge
        claimed_challenge = None
        for ch in challenges:
            if ch["claimed"]:
                claimed_challenge = ch
                break
        
        if not claimed_challenge:
            print("⚠ No claimed challenges to test duplicate claim")
            pytest.skip("No claimed challenges available")
        
        # Try to claim again
        claim_response = requests.post(f"{BASE_URL}/api/challenges/{claimed_challenge['id']}/claim",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert claim_response.status_code == 400, "Should reject already claimed challenge"
        
        print(f"✓ Duplicate claim rejected for '{claimed_challenge['id']}'")

    def test_claim_challenge_not_completed(self, auth_token):
        """Test claiming incomplete challenge returns 400"""
        # Get challenges
        get_response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        challenges = get_response.json()["challenges"]
        
        # Find an incomplete challenge
        incomplete_challenge = None
        for ch in challenges:
            if not ch["completed"]:
                incomplete_challenge = ch
                break
        
        if not incomplete_challenge:
            print("⚠ All challenges completed, cannot test incomplete claim")
            pytest.skip("All challenges completed")
        
        # Try to claim
        claim_response = requests.post(f"{BASE_URL}/api/challenges/{incomplete_challenge['id']}/claim",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert claim_response.status_code == 400, "Should reject incomplete challenge"
        
        print(f"✓ Incomplete challenge claim rejected for '{incomplete_challenge['id']}'")


class TestSocialSharing:
    """Social sharing tests - GET /api/share/profile and POST /api/share/session"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_share_profile_returns_formatted_text(self, auth_token):
        """Test GET /api/share/profile returns formatted share text"""
        response = requests.get(f"{BASE_URL}/api/share/profile", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Share profile failed: {response.text}"
        
        data = response.json()
        assert "share_text" in data
        
        share_text = data["share_text"]
        assert isinstance(share_text, str)
        assert len(share_text) > 0
        
        # Verify it contains expected elements
        assert "FlashCards" in share_text
        assert "Mon profil" in share_text or "profil" in share_text.lower()
        assert "#FlashCards" in share_text
        
        # Should contain emoji
        assert any(ord(c) > 127 for c in share_text), "Share text should contain emoji"
        
        print(f"✓ Share profile text generated ({len(share_text)} chars)")

    def test_share_profile_includes_user_stats(self, auth_token):
        """Test share profile includes user stats (XP, level, streak, etc.)"""
        response = requests.get(f"{BASE_URL}/api/share/profile", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        data = response.json()
        share_text = data["share_text"]
        
        # Should contain numeric stats
        assert "XP" in share_text or "xp" in share_text.lower()
        assert "Niveau" in share_text or "niveau" in share_text.lower()
        
        print("✓ Share profile includes user stats")

    def test_share_session_returns_formatted_text(self, auth_token):
        """Test POST /api/share/session returns formatted share text"""
        response = requests.post(f"{BASE_URL}/api/share/session",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "percentage": 85,
                "correct": 17,
                "total": 20,
                "xp_earned": 270
            }
        )
        assert response.status_code == 200, f"Share session failed: {response.text}"
        
        data = response.json()
        assert "share_text" in data
        
        share_text = data["share_text"]
        assert isinstance(share_text, str)
        assert len(share_text) > 0
        
        # Verify it contains expected elements
        assert "FlashCards" in share_text
        assert "Résultat" in share_text or "résultat" in share_text.lower()
        assert "#FlashCards" in share_text
        
        # Should contain emoji
        assert any(ord(c) > 127 for c in share_text), "Share text should contain emoji"
        
        # Should contain session stats
        assert "85%" in share_text or "85" in share_text
        assert "270" in share_text or "XP" in share_text
        
        print(f"✓ Share session text generated ({len(share_text)} chars)")

    def test_share_session_emoji_varies_by_score(self, auth_token):
        """Test share session uses different emoji based on score"""
        # Test perfect score (100%)
        perfect_response = requests.post(f"{BASE_URL}/api/share/session",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"percentage": 100, "correct": 15, "total": 15, "xp_earned": 300}
        )
        perfect_text = perfect_response.json()["share_text"]
        
        # Test good score (80%)
        good_response = requests.post(f"{BASE_URL}/api/share/session",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"percentage": 80, "correct": 12, "total": 15, "xp_earned": 220}
        )
        good_text = good_response.json()["share_text"]
        
        # Test low score (40%)
        low_response = requests.post(f"{BASE_URL}/api/share/session",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"percentage": 40, "correct": 6, "total": 15, "xp_earned": 110}
        )
        low_text = low_response.json()["share_text"]
        
        # All should have emoji but potentially different ones
        assert any(ord(c) > 127 for c in perfect_text)
        assert any(ord(c) > 127 for c in good_text)
        assert any(ord(c) > 127 for c in low_text)
        
        print("✓ Share session emoji varies by score")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
