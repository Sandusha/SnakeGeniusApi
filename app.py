from flask import Flask, request, jsonify
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.mobilenet import preprocess_input
import numpy as np
from flask_cors import CORS, cross_origin
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from PIL import Image
import io
import uuid
import os
from bson import ObjectId


app = Flask(__name__)
uri = "mongodb+srv://nemezis:Coc12345@snakeg1.dc5b1p2.mongodb.net/?retryWrites=true&w=majority"
CORS(app)  # Enable CORS for all origins

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Load your trained snake prediction model
model = load_model("mobilenet-ft.h5")

# Define your list of snake classes
class_list = ["cobra", "common Krait", "Hump nosed pit viper", "Python", "Rat snake", "russell's viper", "Saw Scaled Viper"]


def serialize_snake(snake):
    # Convert ObjectId to string for JSON serialization
    snake['_id'] = str(snake['_id'])
    return snake
@app.route("/", methods=["GET"])
def home():
    """Serves a basic message for the root path."""
    return "Snake Prediction API is running!"


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
@cross_origin()
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

            # Return prediction results as JSON
            return jsonify({"snake": predicted_snake, "accuracy": accuracy_percentage})

        except FileNotFoundError:
            return jsonify({"error": "Uploaded file not found."}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid request method. Use POST."}), 405


if __name__ == "__main__":
    app.run(debug=True)