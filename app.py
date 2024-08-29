from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.mobilenet import preprocess_input
import numpy as np
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from PIL import Image
import io
import uuid
import os
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['JWT_SECRET_KEY'] = '22769be494538c5d3820475f3ea5ac2906dd240c34937562444d6eb293bcc22e'  # Change this to a secure key
jwt = JWTManager(app)
uri = "mongodb+srv://nemezis:Coc12345@snakeg1.dc5b1p2.mongodb.net/?retryWrites=true&w=majority"
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all origins

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.SnakesG1
users_collection = db.users

# Load your trained snake prediction model
model = load_model("mobilenet-ft.h5")

# Define your list of snake classes
class_list = ["cobra", "common Krait", "Hump nosed pit viper", "Python", "Rat snake", "russell's viper", "Saw Scaled Viper"]

def serialize_snake(snake):
    # Convert ObjectId to string for JSON serialization
    snake['_id'] = str(snake['_id'])
    return snake

def save_prediction(user_id, snake, accuracy):
    timestamp = datetime.utcnow().isoformat()
    prediction = {
        "snake": snake,
        "accuracy": accuracy,
        "timestamp": timestamp
    }
    
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"recent_predictions": prediction}}
    )

    # Debugging statements
    print("Update result matched_count:", result.matched_count)
    print("Update result modified_count:", result.modified_count)

    if result.matched_count == 0:
        print("No user found with ID:", user_id)
    if result.modified_count == 0:
        print("No update performed for user ID:", user_id)

    return result


@app.route("/", methods=["GET"])
def home():
    """Serves a basic message for the root path."""
    return "Snake Prediction API is running!"

def serialize_user(user):
    user['_id'] = str(user['_id'])
    return user

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = {
        "email": data['email'],
        "password": hashed_password,
        "recent_predictions": []
    }

    try:
        db.users.insert_one(user)
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    user = db.users.find_one({"email": data['email']})
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        access_token = create_access_token(identity=str(user['_id']))
        return jsonify({"token": access_token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/account/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        return jsonify({"recent_predictions": user['recent_predictions']}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/account/changepassword', methods=['PUT'])
@jwt_required()
def change_password():
    data = request.json
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({"error": "Old and new password are required"}), 400

    user_id = get_jwt_identity()
    user = db.users.find_one({"_id": ObjectId(user_id)})

    if user and bcrypt.check_password_hash(user['password'], data['old_password']):
        hashed_password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})
        return jsonify({"message": "Password updated successfully"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/addsnake", methods=["POST"])
def add_snake():
    data = request.json  # Assuming request contains JSON data with snake info
    if data:
        try:
            db = client.SnakesG1  # Access the database
            collection = db.snakes  # Access the collection
            inserted_id = collection.insert_one(data).inserted_id
            return jsonify({"message": "Snake added successfully", "id": str(inserted_id)})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No data provided"}), 400
    
@app.route("/updatesnake/<name>", methods=["PUT"])
def update_snake(name):
    data = request.json
    if data:
        try:
            db = client.SnakesG1
            collection = db.snakes
            result = collection.update_one({"name": name}, {"$set": data})

            if result.modified_count > 0:
                return jsonify({"message": f"Snake '{name}' updated successfully"})
            else:
                return jsonify({"error": f"Snake '{name}' not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No data provided"}), 400

@app.route("/deletesnake/<name>", methods=["DELETE"])
def delete_snake(name):
    try:
        db = client.SnakesG1
        collection = db.snakes
        result = collection.delete_one({"name": name})

        if result.deleted_count > 0:
            return jsonify({"message": f"Snake '{name}' deleted successfully"})
        else:
            return jsonify({"error": f"Snake '{name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/searchsnake/<name>", methods=["GET"])
def search_snake(name):
    try:
        db = client.SnakesG1  # Access the database
        collection = db.snakes
        snake = collection.find_one({"name": name})

        if snake:
            serialized_snake = serialize_snake(snake)
            return jsonify({"snake": serialized_snake})
        else:
            return jsonify({"error": "Snake not found."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/snakes", methods=["GET"])
def get_snakes():
    try:
        db = client.SnakesG1  # Access the database
        collection = db.snakes
        snakes = list(collection.find({}))

        # Serialize each snake document
        serialized_snakes = [serialize_snake(snake) for snake in snakes]

        return jsonify({"snakes": serialized_snakes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
@jwt_required(optional=True)  # Allow this route to be accessed both with and without JWT
def predict():
    if request.method == "POST":
        try:
            file = request.files["image"]

            # Generate a unique filename using UUID
            unique_filename = str(uuid.uuid4()) + ".jpg"

            # Construct the path to save the file within the 'static' folder
            save_path = os.path.join("static", unique_filename)

            # Save the uploaded image to the specified path
            file.save(save_path)

            # Read the image file
            img = image.load_img(save_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = preprocess_input(img_array)
            img_array = np.expand_dims(img_array, axis=0)

            # Make predictions
            predictions = model.predict(img_array)
            predicted_class_index = np.argmax(predictions)
            predicted_snake = class_list[predicted_class_index]
            accuracy_percentage = round(predictions[0][predicted_class_index] * 100, 2)

            # Debugging statements
            print("Predicted snake:", predicted_snake)
            print("Accuracy percentage:", accuracy_percentage)

            # Save the prediction if the user is logged in
            current_user_id = get_jwt_identity()
            if current_user_id:
                print("Logged in user ID:", current_user_id)
                save_prediction(current_user_id, predicted_snake, accuracy_percentage)
                print("Prediction saved to MongoDB")

            # Return prediction results as JSON
            return jsonify({"snake": predicted_snake, "accuracy": accuracy_percentage})

        except FileNotFoundError:
            return jsonify({"error": "Uploaded file not found."}), 400
        except Exception as e:
            print("Error during prediction:", str(e))
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid request method. Use POST."}), 405

if __name__ == "__main__":
    app.run(debug=True)
