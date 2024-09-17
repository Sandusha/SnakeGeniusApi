Snake Species Identification API

This Flask-based API uses a pre-trained MobileNet model to predict snake species from an uploaded image. It also provides user authentication, snake management, and prediction history features, with data stored in a MongoDB database.
Features

    User Registration & Authentication: Secure user registration and login using JWT and password hashing.
    Snake Prediction: Upload an image to get predictions for 7 different snake species.
    Prediction History: Logged-in users can save and view their prediction history.
    Snake Management: Admins can add, update, and delete snake information.
    Database: MongoDB integration for storing user data, predictions, and snake information.
    JWT Protected Routes: Certain routes require users to be authenticated via JWT tokens.

Tech Stack

    Flask: Backend framework
    Keras & MobileNet: Used for snake species identification
    MongoDB: Database for storing user data and snake information
    Flask-JWT-Extended: For JWT-based authentication
    Flask-Bcrypt: For password hashing
    Flask-CORS: To enable Cross-Origin Resource Sharing
    Pillow: For image processing
    dotenv: For environment variables management

Setup and Installation

    Clone the repository:

    bash

git clone https://github.com/yourusername/snake-prediction-api.git
cd snake-prediction-api

Create a virtual environment and activate it:

bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install the required dependencies:

bash

pip install -r requirements.txt

Set up environment variables:

    Create a .env file in the root directory and add the following:

    makefile

    JWT_SECRET_KEY=your_jwt_secret_key
    MONGO_URI=your_mongo_database_uri

Ensure the MobileNet model file (mobilenet-ft.h5) is in the project directory. You can download or train this file beforehand.

Run the Flask application:

bash

    python app.py

    The app will be running on http://127.0.0.1:5000/.

API Endpoints
Authentication

    POST /register
    Register a new user.
    Request Body:

    json

{
    "email": "user@example.com",
    "password": "your_password"
}

Response:

json

{
    "message": "User registered successfully"
}

POST /login
Login with email and password.
Request Body:

json

{
    "email": "user@example.com",
    "password": "your_password"
}

Response:

json

    {
        "token": "your_jwt_token",
        "user_id": "your_user_id"
    }

Snake Prediction

    POST /predict
    Upload an image to predict the snake species.
    Request: Upload an image file in the form data field image.
    Response:

    json

    {
        "snake": "Python",
        "accuracy": 95.23
    }

Account Management

    GET /account/predictions
    Get the list of recent predictions for the logged-in user (JWT required).

    PUT /account/changepassword
    Change the password of a logged-in user.
    Request Body:

    json

    {
        "old_password": "old_password",
        "new_password": "new_password"
    }

Snake Management

    POST /addsnake
    Add a new snake species (admin access required).

    PUT /updatesnake/<name>
    Update an existing snake species (admin access required).

    DELETE /deletesnake/<name>
    Delete a snake species by name (admin access required).

    GET /snakelist
    Get a list of all snake names.

    GET /searchsnake/<name>
    Search for a snake by its name.

MongoDB Collections

    Users: Stores user details such as email, hashed passwords, and prediction history.
    Snakes: Stores snake species information (e.g., name, description, image, endemism).

MobileNet Model

The app uses a fine-tuned MobileNet model (mobilenet-ft.h5) to classify 7 different snake species:

    Cobra
    Common Krait
    Hump-nosed Pit Viper
    Python
    Rat Snake
    Russell's Viper
    Saw Scaled Viper

License

This project is licensed under the MIT License. See the LICENSE file for details.
