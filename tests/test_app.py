"""
FastAPI tests for Mergington High School activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to default state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield
    activities.clear()


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        # Arrange
        # (activities fixture already sets up test data)

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        # Arrange
        # (activities fixture already sets up test data)

        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]

        # Assert
        assert response.status_code == 200
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants(self, client):
        """Test that participants are returned correctly"""
        # Arrange
        expected_participant_count = 2

        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]

        # Assert
        assert response.status_code == 200
        assert len(chess_club["participants"]) == expected_participant_count
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert activities[activity_name]["participants"][-1] == new_email

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client):
        """Test that a student cannot sign up twice"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert data["detail"] == "Student is already signed up"

    def test_signup_multiple_students(self, client):
        """Test multiple different students signing up"""
        # Arrange
        activity_name = "Chess Club"
        student1_email = "student1@mergington.edu"
        student2_email = "student2@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student1_email}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student2_email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 2
        assert student1_email in activities[activity_name]["participants"]
        assert student2_email in activities[activity_name]["participants"]


class TestUnregister:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        data = response.json()
        final_count = len(activities[activity_name]["participants"])

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in data["message"]
        assert final_count == initial_count - 1
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert data["detail"] == "Activity not found"

    def test_unregister_not_registered_student(self, client):
        """Test unregister for student not registered"""
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert data["detail"] == "Student is not registered for this activity"

    def test_unregister_then_signup_again(self, client):
        """Test that a student can sign up after unregistering"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
