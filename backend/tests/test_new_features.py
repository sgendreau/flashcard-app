"""
Backend API Tests for New Features (Iteration 2)
Tests: Grade Filtering, User Settings (grade/notifications), Classes (create/join/share), Export/Import
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


class TestGradeFiltering:
    """Grade level filtering tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_get_subjects_with_grade_filter(self, auth_token):
        """Test GET /api/subjects?grade=terminale returns only subjects with terminale cards"""
        response = requests.get(f"{BASE_URL}/api/subjects?grade=terminale", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get subjects with grade filter failed: {response.text}"
        
        data = response.json()
        assert "subjects" in data
        assert "grade_levels" in data
        
        subjects = data["subjects"]
        # Verify all subjects have card_count > 0 (filtered subjects with 0 cards should be excluded)
        for subject in subjects:
            assert subject["card_count"] > 0, f"Subject {subject['id']} has 0 cards but wasn't filtered out"
        
        # Philosophie should be in the list (terminale only)
        subject_ids = [s["id"] for s in subjects]
        assert "philosophie" in subject_ids, "Philosophie (terminale only) should be in filtered results"
        
        print(f"✓ Grade filter 'terminale' returned {len(subjects)} subjects with cards")

    def test_get_subjects_with_college_grade(self, auth_token):
        """Test GET /api/subjects?grade=6eme returns college-level subjects"""
        response = requests.get(f"{BASE_URL}/api/subjects?grade=6eme", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        subjects = data["subjects"]
        
        # Philosophie should NOT be in 6eme results (terminale only)
        subject_ids = [s["id"] for s in subjects]
        assert "philosophie" not in subject_ids, "Philosophie should not appear in 6eme filter"
        
        print(f"✓ Grade filter '6eme' returned {len(subjects)} subjects (philosophie excluded)")

    def test_get_subjects_without_grade_filter(self, auth_token):
        """Test GET /api/subjects without grade filter returns all subjects"""
        response = requests.get(f"{BASE_URL}/api/subjects", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        subjects = data["subjects"]
        # Should return all 9 subjects, but some may have 0 cards after testing
        assert len(subjects) >= 8, f"Expected at least 8 subjects without filter, got {len(subjects)}"
        
        print(f"✓ No grade filter returned {len(subjects)} subjects")


class TestUserSettings:
    """User settings tests (grade level, notifications)"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_update_user_grade_level(self, auth_token):
        """Test PUT /api/user/grade to set user's grade level"""
        response = requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"grade_level": "terminale"}
        )
        assert response.status_code == 200, f"Update grade failed: {response.text}"
        
        data = response.json()
        assert data["grade_level"] == "terminale"
        
        # Verify persistence by getting user info
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        user = me_response.json()["user"]
        assert user["grade_level"] == "terminale", "Grade level not persisted"
        
        print("✓ User grade level updated to 'terminale' and persisted")

    def test_update_user_grade_to_null(self, auth_token):
        """Test PUT /api/user/grade with null to clear grade filter"""
        response = requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"grade_level": None}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["grade_level"] is None
        
        print("✓ User grade level cleared (set to null)")

    def test_update_invalid_grade_level(self, auth_token):
        """Test PUT /api/user/grade with invalid grade"""
        response = requests.put(f"{BASE_URL}/api/user/grade",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"grade_level": "invalid_grade"}
        )
        assert response.status_code == 400, "Should reject invalid grade level"
        
        print("✓ Invalid grade level rejected")

    def test_update_notifications(self, auth_token):
        """Test PUT /api/user/notifications"""
        response = requests.put(f"{BASE_URL}/api/user/notifications",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"notification_enabled": True, "notification_hour": 18}
        )
        assert response.status_code == 200, f"Update notifications failed: {response.text}"
        
        data = response.json()
        assert data["notification_enabled"] is True
        assert data["notification_hour"] == 18
        
        # Verify persistence
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        user = me_response.json()["user"]
        assert user["notification_enabled"] is True
        assert user["notification_hour"] == 18
        
        print("✓ Notification settings updated and persisted")


class TestClasses:
    """Class mode tests (create, join, share decks)"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    @pytest.fixture
    def student_token(self):
        """Create a test student for join tests"""
        timestamp = int(time.time())
        test_email = f"test_student_class_{timestamp}@flashcards.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student Class",
            "email": test_email,
            "password": "test1234"
        })
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            pytest.skip(f"Student registration failed: {response.text}")
        return response.json()["access_token"]

    def test_create_class(self, auth_token):
        """Test POST /api/classes to create a new class"""
        timestamp = int(time.time())
        response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": f"Test Class {timestamp}"}
        )
        assert response.status_code == 200, f"Create class failed: {response.text}"
        
        data = response.json()
        assert "class" in data
        cls = data["class"]
        assert "id" in cls
        assert "code" in cls
        assert "name" in cls
        assert cls["name"] == f"Test Class {timestamp}"
        assert len(cls["code"]) == 6, "Class code should be 6 characters"
        assert "members" in cls
        assert len(cls["members"]) == 1, "Creator should be first member"
        assert cls["members"][0]["role"] == "admin"
        
        print(f"✓ Class created with code: {cls['code']}")

    def test_join_class(self, auth_token, student_token):
        """Test POST /api/classes/join to join a class with code"""
        # Create a class first
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Join Test Class"}
        )
        class_code = create_response.json()["class"]["code"]
        
        # Join with student account
        join_response = requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"code": class_code}
        )
        assert join_response.status_code == 200, f"Join class failed: {join_response.text}"
        
        data = join_response.json()
        assert "class" in data
        cls = data["class"]
        assert len(cls["members"]) == 2, "Should have 2 members after join"
        
        member_roles = [m["role"] for m in cls["members"]]
        assert "admin" in member_roles
        assert "member" in member_roles
        
        print(f"✓ Student joined class {class_code}, now has {len(cls['members'])} members")

    def test_join_class_invalid_code(self, student_token):
        """Test joining with invalid code"""
        response = requests.post(f"{BASE_URL}/api/classes/join",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"code": "INVALID"}
        )
        assert response.status_code == 404, "Should return 404 for invalid code"
        
        print("✓ Invalid class code rejected")

    def test_get_my_classes(self, auth_token):
        """Test GET /api/classes to get user's classes"""
        # Create a class first
        requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "My Classes Test"}
        )
        
        # Get classes
        response = requests.get(f"{BASE_URL}/api/classes", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get classes failed: {response.text}"
        
        data = response.json()
        assert "classes" in data
        classes = data["classes"]
        assert len(classes) > 0, "Should have at least one class"
        
        # Verify class structure
        for cls in classes:
            assert "id" in cls
            assert "name" in cls
            assert "code" in cls
            assert "member_count" in cls
            assert "deck_count" in cls
        
        print(f"✓ Got {len(classes)} classes for user")

    def test_get_class_detail(self, auth_token):
        """Test GET /api/classes/{class_id}"""
        # Create a class
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Detail Test Class"}
        )
        class_id = create_response.json()["class"]["id"]
        
        # Get class detail
        response = requests.get(f"{BASE_URL}/api/classes/{class_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Get class detail failed: {response.text}"
        
        data = response.json()
        assert "class" in data
        cls = data["class"]
        assert cls["id"] == class_id
        assert "shared_decks" in cls
        
        print(f"✓ Got class detail for {class_id}")

    def test_share_deck_to_class(self, auth_token):
        """Test POST /api/classes/{class_id}/share to share a deck"""
        # Create a class
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Share Deck Test"}
        )
        class_id = create_response.json()["class"]["id"]
        
        # Share maths deck
        share_response = requests.post(f"{BASE_URL}/api/classes/{class_id}/share",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"subject_id": "maths", "name": "Maths Deck"}
        )
        assert share_response.status_code == 200, f"Share deck failed: {share_response.text}"
        
        data = share_response.json()
        assert "deck" in data
        deck = data["deck"]
        assert deck["subject_id"] == "maths"
        assert deck["name"] == "Maths Deck"
        assert deck["class_id"] == class_id
        assert "card_ids" in deck
        assert deck["card_count"] > 0
        
        print(f"✓ Shared deck with {deck['card_count']} cards to class")

    def test_study_shared_deck(self, auth_token):
        """Test GET /api/classes/{class_id}/decks/{deck_id}/study"""
        # Create class and share deck
        create_response = requests.post(f"{BASE_URL}/api/classes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Study Shared Deck Test"}
        )
        class_id = create_response.json()["class"]["id"]
        
        share_response = requests.post(f"{BASE_URL}/api/classes/{class_id}/share",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"subject_id": "francais", "name": "Français Deck"}
        )
        deck_id = share_response.json()["deck"]["id"]
        
        # Study the shared deck
        study_response = requests.get(f"{BASE_URL}/api/classes/{class_id}/decks/{deck_id}/study",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert study_response.status_code == 200, f"Study shared deck failed: {study_response.text}"
        
        data = study_response.json()
        assert "session_cards" in data
        assert "total" in data
        assert "subject_id" in data
        assert data["subject_id"] == "francais"
        assert len(data["session_cards"]) > 0
        
        print(f"✓ Started study session with {len(data['session_cards'])} cards from shared deck")


class TestExportImport:
    """Export/Import deck tests"""

    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@flashcards.com",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_export_deck(self, auth_token):
        """Test GET /api/export/{subject_id}"""
        response = requests.get(f"{BASE_URL}/api/export/maths", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200, f"Export deck failed: {response.text}"
        
        data = response.json()
        assert "export" in data
        export = data["export"]
        
        assert "version" in export
        assert export["version"] == "1.0"
        assert "subject" in export
        assert export["subject"] == "Maths"
        assert "subject_id" in export
        assert export["subject_id"] == "maths"
        assert "cards" in export
        assert "card_count" in export
        assert len(export["cards"]) == export["card_count"]
        assert "exported_at" in export
        assert "exported_by" in export
        
        # Verify card structure
        for card in export["cards"]:
            assert "question" in card
            assert "answer" in card
            assert "grade_levels" in card
        
        print(f"✓ Exported {export['card_count']} cards from maths")

    def test_import_deck(self, auth_token):
        """Test POST /api/import"""
        # First export a deck
        export_response = requests.get(f"{BASE_URL}/api/export/svt", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        export_data = export_response.json()["export"]
        
        # Import to same subject (should add duplicate cards)
        import_response = requests.post(f"{BASE_URL}/api/import",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "subject_id": "svt",
                "cards": export_data["cards"]
            }
        )
        assert import_response.status_code == 200, f"Import deck failed: {import_response.text}"
        
        data = import_response.json()
        assert "imported" in data
        assert "subject_id" in data
        assert data["subject_id"] == "svt"
        assert data["imported"] == len(export_data["cards"])
        
        print(f"✓ Imported {data['imported']} cards to {data['subject_id']}")

    def test_import_invalid_deck(self, auth_token):
        """Test importing with invalid subject_id"""
        response = requests.post(f"{BASE_URL}/api/import",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "subject_id": "invalid_subject",
                "cards": [{"question": "Q", "answer": "A"}]
            }
        )
        assert response.status_code == 404, "Should reject invalid subject_id"
        
        print("✓ Invalid subject_id rejected during import")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
