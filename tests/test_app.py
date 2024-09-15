import pytest
from app import app, db, users_collection, snakes_collection
from flask_jwt_extended import create_access_token
import json
from datetime import datetime
import uuid
import io

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    # Clean up the test database after each test
    db.users.drop()
    db.snakes.drop()

# Test Home Route
def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Snake Prediction API is running!" in response.data

# Test User Registration
def test_register(client):
    data = {
        "email": "test@test.com",
        "password": "password123"
    }
    response = client.post('/register', json=data)
    assert response.status_code == 201
    assert b"User registered successfully" in response.data

    # Check if user is added to the test DB
    user = users_collection.find_one({"email": "test@test.com"})
    assert user is not None

# Test Duplicate User Registration
def test_register_duplicate(client):
    data = {
        "email": "test@test.com",
        "password": "password123"
    }
    client.post('/register', json=data)  # First registration
    response = client.post('/register', json=data)  # Duplicate
    assert response.status_code == 400
    assert b"Email is already registered" in response.data

# Test User Login
def test_login(client):
    # Register the user first
    client.post('/register', json={"email": "test@test.com", "password": "password123"})
    
    # Attempt to login
    login_data = {
        "email": "test@test.com",
        "password": "password123"
    }
    response = client.post('/login', json=login_data)
    assert response.status_code == 200
    assert "token" in json.loads(response.data)

# Test Login with Invalid Credentials
def test_login_invalid_credentials(client):
    data = {
        "email": "test@test.com",
        "password": "wrongpassword"
    }
    response = client.post('/login', json=data)
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data

# Test Add Snake
def test_add_snake(client):
    data = {
        "name": "Test Snake",
        "image": "https://example.com/test.jpg",
        "description": "Test description",
        "endemism": "Endemic",
        "wikiLink": "https://en.wikipedia.org/wiki/Test_Snake"
    }
    response = client.post('/addsnake', json=data)
    assert response.status_code == 200
    assert b"Snake added successfully" in response.data

    # Check if snake is added to the DB
    snake = snakes_collection.find_one({"name": "Test Snake"})
    assert snake is not None

# Test Update Snake
def test_update_snake(client):
    # Add a snake first
    snakes_collection.insert_one({
        "name": "Old Snake",
        "image": "https://example.com/old.jpg",
        "description": "Old description",
        "endemism": "Not Endemic",
        "wikiLink": "https://en.wikipedia.org/wiki/Old_Snake"
    })

    update_data = {
        "description": "Updated description"
    }
    response = client.put('/updatesnake/Old Snake', json=update_data)
    assert response.status_code == 200
    assert b"Snake 'Old Snake' updated successfully" in response.data

    # Check if snake is updated
    snake = snakes_collection.find_one({"name": "Old Snake"})
    assert snake['description'] == "Updated description"

# Test Delete Snake
def test_delete_snake(client):
    # Add a snake first
    snakes_collection.insert_one({
        "name": "Delete Snake",
        "image": "https://example.com/delete.jpg",
        "description": "To be deleted",
        "endemism": "Not Endemic",
        "wikiLink": "https://en.wikipedia.org/wiki/Delete_Snake"
    })

    response = client.delete('/deletesnake/Delete Snake')
    assert response.status_code == 200
    assert b"Snake 'Delete Snake' deleted successfully" in response.data

    # Check if snake is deleted
    snake = snakes_collection.find_one({"name": "Delete Snake"})
    assert snake is None

# Test Search Snake
def test_search_snake(client):
    # Add a snake to the DB
    snakes_collection.insert_one({
        "name": "Test Search Snake",
        "image": "https://example.com/search.jpg",
        "description": "Description for search test",
        "endemism": "Not Endemic",
        "wikiLink": "https://en.wikipedia.org/wiki/Test_Search_Snake"
    })

    response = client.get('/searchsnake/Test Search Snake')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['snake']['name'] == "Test Search Snake"

# Test Load All Snakes
def test_get_snakes(client):
    # Add a snake to the DB
    snakes_collection.insert_one({
        "name": "Test Get Snake",
        "image": "https://example.com/get.jpg",
        "description": "Description for get test",
        "endemism": "Not Endemic",
        "wikiLink": "https://en.wikipedia.org/wiki/Test_Get_Snake"
    })

    response = client.get('/snakes')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert any(snake['name'] == "Test Get Snake" for snake in json_data['snakes'])

# Test Search Snake with Non-existent Snake
def test_search_snake_not_found(client):
    response = client.get('/searchsnake/Nonexistent Snake')
    assert response.status_code == 404
    assert b"Snake not found." in response.data

# Test Snake Prediction
def test_predict(client, monkeypatch):
    # Mock the model prediction to return a known class and accuracy
    def mock_predict(*args, **kwargs):
        return [[0.1, 0.1, 0.1, 0.1, 0.5, 0.1, 0.1]]  # Mock prediction for "Rat snake"

    monkeypatch.setattr("app.model.predict", mock_predict)

    # Upload an image for prediction
    with open('tests/test_image1.jpg', 'rb') as img:
        data = {'image': (img, 'test_image.jpg')}
        response = client.post('/predict', content_type='multipart/form-data', data=data)

    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['snake'] == 'Rat snake'
    assert json_data['accuracy'] == 50.0


# Test Save Prediction
def test_save_prediction(client):
    # Register and login a user
    client.post('/register', json={"email": "test@test.com", "password": "password123"})
    login_response = client.post('/login', json={"email": "test@test.com", "password": "password123"})
    token = json.loads(login_response.data)['token']

    user_id = json.loads(login_response.data)['user_id']  # Assuming you return user_id on login

    # Use a valid image file for testing
    with open('tests/test_image.jpg', 'rb') as image_file:
        response = client.post('/predict', content_type='multipart/form-data', data={'image': (image_file, 'test_image.jpg')}, headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['snake'] is not None
    assert json_data['accuracy'] is not None

    # Fetch predictions
    response = client.get('/account/predictions', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    predictions = json.loads(response.data)['recent_predictions']
    assert any(prediction['snake'] == json_data['snake'] for prediction in predictions)



# Test Predict Endpoint Without JWT
def test_predict_without_jwt(client):
    # Send a prediction request without JWT
    with open('tests/test_image1.jpg', 'rb') as img:
        data = {'image': (img, 'test_image.jpg')}
        response = client.post('/predict', content_type='multipart/form-data', data=data)

    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert json_data['snake'] is not None
    assert json_data['accuracy'] is not None


# Test Account Recent Predictions
def test_get_predictions(client):
    # Register and login a user
    client.post('/register', json={"email": "test@test.com", "password": "password123"})
    login_response = client.post('/login', json={"email": "test@test.com", "password": "password123"})
    token = json.loads(login_response.data)['token']

    # Simulate saving a prediction
    users_collection.update_one({"email": "test@test.com"}, {"$push": {"recent_predictions": {"snake": "cobra", "accuracy": 95.23, "timestamp": "2024-08-27T12:34:56"}}})

    # Fetch predictions
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/account/predictions', headers=headers)
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert len(json_data['recent_predictions']) > 0
    assert json_data['recent_predictions'][0]['snake'] == "cobra"

# Test Change Password
def test_change_password(client):
    # Register and login a user
    client.post('/register', json={"email": "test@test.com", "password": "password123"})
    login_response = client.post('/login', json={"email": "test@test.com", "password": "password123"})
    token = json.loads(login_response.data)['token']

    # Change password
    change_password_data = {
        "old_password": "password123",
        "new_password": "newpassword123"
    }
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/account/changepassword', json=change_password_data, headers=headers)
    assert response.status_code == 200
    assert b"Password updated successfully" in response.data

    
# Test Change Password with Incorrect Old Password
def test_change_password_incorrect_old_password(client):
    # Register and login a user
    client.post('/register', json={"email": "test@test.com", "password": "password123"})
    login_response = client.post('/login', json={"email": "test@test.com", "password": "password123"})
    token = json.loads(login_response.data)['token']

    # Attempt to change password with incorrect old password
    change_password_data = {
        "old_password": "wrongpassword",
        "new_password": "newpassword123"
    }
    headers = {'Authorization': f'Bearer {token}'}
    response = client.put('/account/changepassword', json=change_password_data, headers=headers)
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data