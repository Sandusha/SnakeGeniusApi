from flask import Flask, request, jsonify
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.mobilenet import preprocess_input
import numpy as np
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Load your trained snake prediction model
model = load_model("mobilenet-ft.h5")

# Define your list of snake classes 
class_list = ["cobra", "common_krait", "hump_nosed_pit_viper", "Python", "Rat_snake", "russells_viper", "Saw_Scaled_Viper"]

@app.route("/", methods=["GET"])
def home():
    """Serves a basic message for the root path."""
    return "Snake Prediction API is running!"

@app.route("/predict", methods=["POST"])
def predict():
    if request.method == "POST":
        # Get the uploaded image file
        try:
            file = request.files["image"]
        except KeyError:
            return jsonify({"error": "No image file uploaded!"}), 400

        # Save the file temporarily
        file_path = "static/temp.jpg"
        file.save(file_path)

        # Preprocess the image for prediction
        img = image.load_img(file_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        # Make predictions
        predictions = model.predict(img_array)

        # Get the index of the predicted class
        predicted_class_index = np.argmax(predictions)

        # Get the snake name based on the class index
        predicted_snake = class_list[predicted_class_index]

        # Get the accuracy as a percentage
        accuracy_percentage = round(predictions[0][predicted_class_index] * 100, 2)

        # Return prediction results as JSON
        return jsonify({"snake": predicted_snake, "accuracy": accuracy_percentage})

    else:
        return jsonify({"error": "Invalid request method. Use POST."}), 405

if __name__ == "__main__":
    app.run(debug=True)
