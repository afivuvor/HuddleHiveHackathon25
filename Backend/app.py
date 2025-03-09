from flask import Flask, request, jsonify
import requests
import cv2
import numpy as np
from deepface import DeepFace
from PIL import Image
from pymongo import MongoClient
import gridfs
import io
import urllib.parse
from datetime import datetime

app = Flask(__name__)

# Encode special characters in the password (if any)
# password = urllib.parse.quote_plus("Seeu@the2p")
# MONGO_URI = f"mongodb+srv://afiscapstone:{password}@hackathon1.7z0bt.mongodb.net/?retryWrites=true&w=majority&appName=hackathon1"
MONGO_URI = "mongodb+srv://afiscapstone:Senawillbegr8@hackathon1.7z0bt.mongodb.net/?retryWrites=true&w=majority&appName=hackathon1"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["people_search"]
users_collection = db["users"]
fs = gridfs.GridFS(db)

try:
    print("✅ Connected to MongoDB and GridFS is ready!")
except Exception as e:
    print(f"❌ Connection failed: {e}")

@app.route("/")
def home():
    try:
        # Attempt to retrieve a single document to test the connection
        db.command("ping")  # Simple MongoDB command to check connection
        return "✅ MongoDB is connected!", 200
    except Exception as e:
        return f"❌ MongoDB connection failed: {e}", 500

def download_image(image_data):
    """Convert image data (bytes) to OpenCV format."""
    img_arr = np.asarray(bytearray(image_data), dtype=np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if img is not None:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def match_faces(uploaded_image_path, user_image_id):
    """Match uploaded image with a stored user image."""
    image_data = fs.get(user_image_id).read()
    user_image = download_image(image_data)

    if user_image is None:
        return False

    # Convert uploaded image to OpenCV format
    uploaded_image = cv2.imread(uploaded_image_path)
    if uploaded_image is None:
        return False
    uploaded_image = cv2.cvtColor(uploaded_image, cv2.COLOR_BGR2RGB)

    try:
        result = DeepFace.verify(uploaded_image, user_image, model_name="Facenet512", enforce_detection=False)
        return result.get("verified", False)
    except Exception as e:
        print(f"Face verification error: {e}")
        return False

@app.route("/add_user", methods=["POST"])
def add_user():
    """Endpoint to add a user with an image to MongoDB."""
    data = request.form
    image_file = request.files.get("photo")

    if not image_file:
        return jsonify({"error": "No image uploaded"}), 400

    image_id = fs.put(image_file.read(), filename=image_file.filename)

    # Convert birthday to a Date object
    birthday_str = data.get("birthday")
    try:
        birthday = datetime.strptime(birthday_str, "%d-%m-%Y") if birthday_str else None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use DD-MM-YYYY"}), 400

    user_data = {
        "name": data.get("name"),
        "location": data.get("location"),
        "company": data.get("company"),
        "birthday": birthday,
        "image_id": str(image_id)  # Convert image ID to string for MongoDB storage
    }
    users_collection.insert_one(user_data)

    return jsonify({"message": "User added successfully", "user": user_data})

@app.route("/search_by_image", methods=["POST"])
def search_by_image():
    """Search for users in the DB using face matching."""
    if "file" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["file"]
    image_path = "temp.jpg"
    image_file.save(image_path)
    
    img = Image.open(image_path).convert("RGB")
    img.save(image_path)

    possible_matches = []
    
    users = users_collection.find({})
    for user in users:
        if match_faces(image_path, user["image_id"]):
            possible_matches.append({
                "name": user["name"],
                "location": user["location"],
                "company": user["company"]
            })

    if possible_matches:
        return jsonify({"matches": possible_matches})
    
    return jsonify({"message": "No matches found"})

GITHUB_API_URL = "https://api.github.com/search/users"

def search_github_users(query):
    """Search for users on GitHub using multiple criteria."""
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_API_URL, headers=headers, params={"q": query})
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "GitHub search failed", "status": response.status_code}

@app.route("/search", methods=["GET"])
def search_people():
    """Search GitHub users by name, location, company, followers, or a combination."""
    search_query = []
    
    if request.args.get("name"):
        search_query.append(f"{request.args.get('name')} in:name")
    if request.args.get("location"):
        search_query.append(f"location:{request.args.get('location')}")
    if request.args.get("company"):
        search_query.append(f"company:{request.args.get('company')}")
    if request.args.get("followers"):
        search_query.append(f"followers:>{request.args.get('followers')}")
    
    if not search_query:
        return jsonify({"error": "At least one search parameter is required"}), 400

    final_query = " ".join(search_query)
    github_results = search_github_users(final_query)

    return jsonify(github_results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)  # Allows external access, runs on port 8000