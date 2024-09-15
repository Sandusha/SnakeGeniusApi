# conftest.py

import pytest
from app import app as flask_app
from flask_jwt_extended import create_access_token
from pymongo import MongoClient

@pytest.fixture(scope='module')
def test_client():
    flask_app.config['TESTING'] = True
    flask_app.config['MONGODB_URI'] = uri = "mongodb+srv://nemezis:Coc12345@snakeg1.dc5b1p2.mongodb.net/?retryWrites=true&w=majority"  # Test database URI
    with flask_app.test_client() as client:
        yield client

@pytest.fixture(scope='module')
def init_db():
    client = MongoClient(uri = "mongodb+srv://nemezis:Coc12345@snakeg1.dc5b1p2.mongodb.net/?retryWrites=true&w=majority")
    db = client.get_database()
    db.Users.drop()  # Ensure test collections are empty before each test
    yield db
    db.Users.drop()
